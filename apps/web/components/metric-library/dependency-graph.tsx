"use client";

// 指标依赖图谱（D040/D047 内部指标库 v1.1）。
// v2（2026-09-16）：渲染层从手写 SVG 迁移到 @xyflow/react（reactflow），
// 白得平移/缩放/MiniMap/节点拖拽/fitView；分层布局算法与上下游闭包高亮
// 为 FLOW 自有业务逻辑，保持原样（确定性分层、环兜底、快照可测）。

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { MetricLibraryEntry } from "../../lib/api/client";
import { metricEntryHref, metricFocusHref } from "../../lib/deep-links";
import { VISUAL_TOKENS } from "../../lib/visual-tokens.generated";

const NODE_W = 168;
const NODE_H = 46;
const COL_GAP = 84;
const ROW_GAP = 18;
const PADDING = 24;
const GRAPH_EDGE = VISUAL_TOKENS["colors-line-default"];
const GRAPH_ACTIVE_EDGE = VISUAL_TOKENS["colors-brand-gold"];
const GRAPH_TEXT = VISUAL_TOKENS["colors-text-primary"];
const GRAPH_MUTED = VISUAL_TOKENS["colors-text-muted"];

type GraphNodeData = {
  entry: MetricLibraryEntry;
  domainLabel: string;
  domainColor: string;
  selected: boolean;
  dim: boolean;
  onActivate: (id: string) => void;
};

type Layout = {
  positions: Map<string, { x: number; y: number }>;
  cyclic: string[];
};

function graphNodeId(metric: MetricLibraryEntry): string {
  return metric.entry_id
    ? `entry:${metric.entry_id}`
    : `metric:${metric.collection ?? metric.domain}:${metric.metric_code}:${metric.name}`;
}

/** 指标编码跨 collection 可复用；先在同 collection 内解析，避免把两套口径误连。 */
function dependencyIndex(metrics: MetricLibraryEntry[]): Map<string, string[]> {
  const byCode = new Map<string, MetricLibraryEntry[]>();
  for (const metric of metrics) {
    byCode.set(metric.metric_code, [...(byCode.get(metric.metric_code) ?? []), metric]);
  }

  return new Map(metrics.map((metric) => {
    const dependencies = (metric.depends_on ?? []).flatMap((code) => {
      const candidates = byCode.get(code) ?? [];
      const sameCollection = candidates.filter((candidate) => candidate.collection === metric.collection);
      const resolved = sameCollection.length === 1
        ? sameCollection[0]
        : candidates.length === 1
          ? candidates[0]
          : undefined;
      return resolved ? [graphNodeId(resolved)] : [];
    });
    return [graphNodeId(metric), dependencies];
  }));
}

/** 最长路径分层 + 层内按 code 排序；环依赖节点兜底到最后一层并标记 cyclic。 */
function computeLayout(metrics: MetricLibraryEntry[], deps: Map<string, string[]>): Layout {
  const byId = new Map(metrics.map((metric) => [graphNodeId(metric), metric]));

  const layerOf = new Map<string, number>();
  const visiting = new Set<string>();
  const cyclic: string[] = [];

  const resolve = (code: string): number => {
    const known = layerOf.get(code);
    if (known !== undefined) return known;
    if (visiting.has(code)) {
      cyclic.push(code);
      layerOf.set(code, 0);
      return 0;
    }
    visiting.add(code);
    const list = deps.get(code) ?? [];
    const layer = list.length === 0 ? 0 : 1 + Math.max(...list.map(resolve));
    visiting.delete(code);
    layerOf.set(code, layer);
    return layer;
  };
  for (const id of byId.keys()) resolve(id);

  const maxLayer = Math.max(0, ...layerOf.values());
  const buckets: string[][] = Array.from({ length: maxLayer + 1 }, () => []);
  for (const id of [...byId.keys()].sort()) buckets[layerOf.get(id) ?? 0].push(id);

  const positions = new Map<string, { x: number; y: number }>();
  buckets.forEach((codes, layer) => {
    codes.forEach((code, i) => {
      positions.set(code, {
        x: PADDING + layer * (NODE_W + COL_GAP),
        y: PADDING + i * (NODE_H + ROW_GAP),
      });
    });
  });
  return { positions, cyclic };
}

/** 传递闭包：上游=该指标依赖的全体；下游=依赖该指标的全体。 */
function closure(
  edges: Map<string, string[]>,
  reverseIndex: Map<string, string[]>,
  start: string,
  direction: "up" | "down",
): Set<string> {
  const out = new Set<string>();
  const stack = [start];
  while (stack.length > 0) {
    const cur = stack.pop()!;
    const nexts = direction === "up" ? (edges.get(cur) ?? []) : (reverseIndex.get(cur) ?? []);
    for (const next of nexts) {
      if (next !== start && !out.has(next)) {
        out.add(next);
        stack.push(next);
      }
    }
  }
  return out;
}

const DOMAIN_PALETTE: Record<string, string> = {
  solvency: VISUAL_TOKENS["colors-brand-navy"],
  operation: VISUAL_TOKENS["colors-data-cash"],
  profitability: VISUAL_TOKENS["colors-brand-gold"],
  growth: VISUAL_TOKENS["colors-data-series5"],
  cashflow: VISUAL_TOKENS["colors-semantic-positive"],
  value: VISUAL_TOKENS["colors-data-revenue"],
  scale: VISUAL_TOKENS["colors-text-muted"],
};

function MetricNode({ id, data }: NodeProps<Node<GraphNodeData>>) {
  const { entry, domainLabel, domainColor, selected, dim, onActivate } = data;
  return (
    <div
      style={{
        width: NODE_W,
        height: NODE_H,
        borderRadius: 8,
        background: VISUAL_TOKENS["colors-surface-raised"],
        border: `1.5px solid ${selected ? GRAPH_ACTIVE_EDGE : domainColor}`,
        boxShadow: selected ? `0 0 0 2px ${VISUAL_TOKENS["colors-brand-goldSoft"]}` : undefined,
        opacity: dim ? 0.3 : 1,
        padding: "6px 10px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        cursor: "pointer",
        position: "relative",
      }}
      className="ml-graph__node"
      aria-label={`${entry.name}（${entry.metric_code}）`}
      role="button"
      aria-pressed={selected}
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onActivate(id);
        }
      }}
      title={
        `${entry.name} · ${domainLabel}` +
        ((entry.analysis_dimensions ?? []).length > 0
          ? ` · 维度：${entry.analysis_dimensions.join(" / ")}`
          : "")
      }
    >
      <Handle
        id={Position.Left}
        type="target"
        position={Position.Left}
        isConnectable={false}
        style={{ opacity: 0, width: 6, height: 6, border: 0, background: "transparent" }}
      />
      <span style={{ fontSize: 12, fontWeight: 600, color: GRAPH_TEXT, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {entry.name}
      </span>
      <span style={{ fontSize: 11, color: GRAPH_MUTED, fontFamily: VISUAL_TOKENS["typography-family-mono"], whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {entry.metric_code}
      </span>
      {(entry.tier ?? "professional") === "core" ? (
        <span
          style={{ position: "absolute", top: 8, right: 8, width: 8, height: 8, borderRadius: "50%", background: VISUAL_TOKENS["colors-brand-gold"] }}
          title="常用指标"
        />
      ) : null}
      <Handle
        id={Position.Right}
        type="source"
        position={Position.Right}
        isConnectable={false}
        style={{ opacity: 0, width: 6, height: 6, border: 0, background: "transparent" }}
      />
    </div>
  );
}

const nodeTypes = { metric: MetricNode };

export function DependencyGraph({
  metrics,
  domains,
}: {
  metrics: MetricLibraryEntry[];
  domains: Record<string, string>;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const [tierFilter, setTierFilter] = useState<"all" | "core" | "professional">("core");

  const visible = useMemo(
    () => metrics.filter((m) => tierFilter === "all" || (m.tier ?? "professional") === tierFilter),
    [metrics, tierFilter],
  );
  const edgesIndex = useMemo(() => dependencyIndex(visible), [visible]);
  const layout = useMemo(() => computeLayout(visible, edgesIndex), [visible, edgesIndex]);
  const graphHeight = useMemo(
    () => Math.max(560, ...[...layout.positions.values()].map(({ y }) => y + NODE_H + PADDING)),
    [layout],
  );
  const graphWidth = useMemo(
    () => Math.max(560, ...[...layout.positions.values()].map(({ x }) => x + NODE_W + PADDING)),
    [layout],
  );
  const resolvedEdges = useMemo(
    () => new Map([...edgesIndex].map(([id, dependencies]) => [id, dependencies.filter((dependency) => layout.positions.has(dependency))])),
    [edgesIndex, layout],
  );
  const entryByNodeId = useMemo(
    () => new Map(visible.map((metric) => [graphNodeId(metric), metric])),
    [visible],
  );

  const reverseIndex = useMemo(() => {
    const rev = new Map<string, string[]>();
    for (const [from, tos] of resolvedEdges) {
      for (const to of tos) rev.set(to, [...(rev.get(to) ?? []), from]);
    }
    return rev;
  }, [resolvedEdges]);
  const upstream = useMemo(
    () => (selected ? closure(resolvedEdges, reverseIndex, selected, "up") : new Set<string>()),
    [selected, resolvedEdges, reverseIndex],
  );
  const downstream = useMemo(
    () => (selected ? closure(resolvedEdges, reverseIndex, selected, "down") : new Set<string>()),
    [selected, resolvedEdges, reverseIndex],
  );

  const nodes: Node<GraphNodeData>[] = useMemo(
    () =>
      visible.map((entry) => {
        const id = graphNodeId(entry);
        const pos = layout.positions.get(id) ?? { x: PADDING, y: PADDING };
        const isSelected = id === selected;
        const dim =
          selected !== null &&
          !isSelected &&
          !upstream.has(id) &&
          !downstream.has(id);
        return {
          id,
          type: "metric" as const,
          position: pos,
          focusable: false,
          data: {
            entry,
            domainLabel: domains[entry.domain] ?? entry.domain,
            domainColor: DOMAIN_PALETTE[entry.domain] ?? GRAPH_MUTED,
            selected: isSelected,
            dim,
            onActivate: (nodeId: string) => setSelected((current) => current === nodeId ? null : nodeId),
          },
        };
      }),
    [visible, layout, selected, upstream, downstream, domains],
  );

  const edges: Edge[] = useMemo(() => {
    const list: Edge[] = [];
    for (const [code, deps] of resolvedEdges) {
      for (const dep of deps) {
        const active =
          selected !== null &&
          (upstream.has(dep) || dep === selected) &&
          (code === selected || downstream.has(code) || upstream.has(code));
        list.push({
          id: `${dep}->${code}`,
          source: dep,
          target: code,
          sourceHandle: Position.Right,
          targetHandle: Position.Left,
          animated: active,
          style: {
            stroke: active ? GRAPH_ACTIVE_EDGE : GRAPH_EDGE,
            strokeWidth: active ? 2 : 1,
            opacity: selected !== null && !active ? 0.25 : 1,
          },
        });
      }
    }
    return list;
  }, [resolvedEdges, selected, upstream, downstream]);

  const edgeCount = [...resolvedEdges.values()].flat().length;
  const selectedEntry = selected ? entryByNodeId.get(selected) : undefined;
  const selectedHref = selectedEntry?.entry_id
    ? metricEntryHref(selectedEntry.entry_id)
    : metricFocusHref(selectedEntry?.metric_code ?? selected ?? "", selectedEntry?.collection);

  return (
    <section className="ml-graph" aria-label="指标依赖图谱">
      <div className="ml-graph__toolbar">
        <p className="ml-graph__hint">
          {visible.length} 个指标、{edgeCount} 条依赖边。
          点击节点查看上下游；颜色为能力域（{Object.values(domains).join(" / ")}）。
          默认聚焦常用指标，可切换全部或专业层；支持缩放/平移/拖拽节点与 MiniMap 导航。
        </p>
        <label className="ml-graph__filter">
          分层{" "}
          <select
            aria-label="分层"
            value={tierFilter}
            onChange={(e) => {
              setSelected(null);
              setTierFilter(e.target.value as typeof tierFilter);
            }}
          >
            <option value="all">全部</option>
            <option value="core">常用</option>
            <option value="professional">专业</option>
          </select>
        </label>
        {selected ? (
          <button type="button" className="ml-graph__clear" onClick={() => setSelected(null)}>
            清除选择
          </button>
        ) : null}
      </div>

      <div
        className="ml-graph__frame"
        role="region"
        aria-label="指标依赖关系有向图（可缩放平移）"
        tabIndex={0}
      >
        <div className="ml-graph__flow" style={{ height: graphHeight, width: graphWidth }}>
          <ReactFlow
            key={tierFilter}
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.15, maxZoom: 1 }}
            minZoom={0.2}
            maxZoom={2}
            nodesDraggable
            nodesConnectable={false}
            onNodeClick={(_event, node) => setSelected((current) => node.id === current ? null : node.id)}
          >
            <Background gap={24} color={VISUAL_TOKENS["colors-line-subtle"]} />
            <Controls showInteractive={false} />
            <MiniMap
              pannable
              zoomable
              nodeColor={(node) => (node.data as GraphNodeData).domainColor}
              nodeStrokeWidth={2}
            />
          </ReactFlow>
        </div>
      </div>
      {layout.cyclic.length > 0 ? (
        <p className="ml-graph__warning" role="note">
          检测到依赖环（已按底层处理）：{layout.cyclic.map((id) => entryByNodeId.get(id)?.name ?? id).join("、")}
        </p>
      ) : null}
      {selected ? (
        <p className="ml-graph__selected" role="status">
          已选中 <strong>{selectedEntry?.name}</strong>
          （上游依赖 {upstream.size} 个、下游引用 {downstream.size} 个，蓝色高亮为直接关联链路）
          {" · "}
          <Link href={selectedHref}>查看指标卡片</Link>
        </p>
      ) : null}
    </section>
  );
}
