"use client";

// 指标依赖图谱（D040/D047 内部指标库 v1.1）。
// v2（2026-09-16）：渲染层从手写 SVG 迁移到 @xyflow/react（reactflow），
// 白得平移/缩放/MiniMap/节点拖拽/fitView；分层布局算法与上下游闭包高亮
// 为 FLOW 自有业务逻辑，保持原样（确定性分层、环兜底、快照可测）。

import { useMemo, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { MetricLibraryEntry } from "../../lib/api/client";

const NODE_W = 168;
const NODE_H = 46;
const COL_GAP = 84;
const ROW_GAP = 18;
const PADDING = 24;

type GraphNodeData = {
  entry: MetricLibraryEntry;
  domainLabel: string;
  domainColor: string;
  selected: boolean;
  dim: boolean;
};

type Layout = {
  positions: Map<string, { x: number; y: number }>;
  cyclic: string[];
};

/** 最长路径分层 + 层内按 code 排序；环依赖节点兜底到最后一层并标记 cyclic。 */
function computeLayout(metrics: MetricLibraryEntry[]): Layout {
  const byCode = new Map(metrics.map((m) => [m.metric_code, m]));
  const deps = new Map<string, string[]>();
  for (const m of metrics) {
    deps.set(
      m.metric_code,
      (m.depends_on ?? []).filter((d) => byCode.has(d) && d !== m.metric_code),
    );
  }

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
  for (const code of byCode.keys()) resolve(code);

  const maxLayer = Math.max(0, ...layerOf.values());
  const buckets: string[][] = Array.from({ length: maxLayer + 1 }, () => []);
  for (const code of [...byCode.keys()].sort()) buckets[layerOf.get(code) ?? 0].push(code);

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
  solvency: "#1d4ed8", operation: "#0f766e", profitability: "#b45309",
  growth: "#7c3aed", cashflow: "#15803d", value: "#be185d", scale: "#475569",
};

function MetricNode({ data }: NodeProps<Node<GraphNodeData>>) {
  const { entry, domainLabel, domainColor, selected, dim } = data;
  return (
    <div
      style={{
        width: NODE_W,
        height: NODE_H,
        borderRadius: 8,
        background: "#fff",
        border: `1.5px solid ${selected ? "#1d4ed8" : domainColor}`,
        boxShadow: selected ? "0 0 0 2px rgba(29,78,216,.25)" : undefined,
        opacity: dim ? 0.3 : 1,
        padding: "6px 10px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        cursor: "pointer",
        position: "relative",
      }}
      aria-label={`${entry.name}（${entry.metric_code}）`}
      role="button"
      title={
        `${entry.name} · ${domainLabel}` +
        ((entry.analysis_dimensions ?? []).length > 0
          ? ` · 维度：${entry.analysis_dimensions.join(" / ")}`
          : "")
      }
    >
      <span style={{ fontSize: 12, fontWeight: 600, color: "#14243a", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {entry.name}
      </span>
      <span style={{ fontSize: 11, color: "#5b6774", fontFamily: "var(--font-mono, monospace)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
        {entry.metric_code}
      </span>
      {(entry.tier ?? "professional") === "core" ? (
        <span
          style={{ position: "absolute", top: 8, right: 8, width: 8, height: 8, borderRadius: "50%", background: "#f59e0b" }}
          title="常用指标"
        />
      ) : null}
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
  const [tierFilter, setTierFilter] = useState<"all" | "core" | "professional">("all");

  const visible = useMemo(
    () => metrics.filter((m) => tierFilter === "all" || (m.tier ?? "professional") === tierFilter),
    [metrics, tierFilter],
  );
  const layout = useMemo(() => computeLayout(visible), [visible]);
  const edgesIndex = useMemo(
    () => new Map(visible.map((m) => [m.metric_code, (m.depends_on ?? []).filter((d) => layout.positions.has(d))])),
    [visible, layout],
  );

  const reverseIndex = useMemo(() => {
    const rev = new Map<string, string[]>();
    for (const [from, tos] of edgesIndex) {
      for (const to of tos) rev.set(to, [...(rev.get(to) ?? []), from]);
    }
    return rev;
  }, [edgesIndex]);
  const upstream = useMemo(
    () => (selected ? closure(edgesIndex, reverseIndex, selected, "up") : new Set<string>()),
    [selected, edgesIndex, reverseIndex],
  );
  const downstream = useMemo(
    () => (selected ? closure(edgesIndex, reverseIndex, selected, "down") : new Set<string>()),
    [selected, edgesIndex, reverseIndex],
  );

  const nodes: Node<GraphNodeData>[] = useMemo(
    () =>
      visible.map((entry) => {
        const pos = layout.positions.get(entry.metric_code) ?? { x: PADDING, y: PADDING };
        const isSelected = entry.metric_code === selected;
        const dim =
          selected !== null &&
          !isSelected &&
          !upstream.has(entry.metric_code) &&
          !downstream.has(entry.metric_code);
        return {
          id: entry.metric_code,
          type: "metric" as const,
          position: pos,
          data: {
            entry,
            domainLabel: domains[entry.domain] ?? entry.domain,
            domainColor: DOMAIN_PALETTE[entry.domain] ?? "#475569",
            selected: isSelected,
            dim,
          },
        };
      }),
    [visible, layout, selected, upstream, downstream, domains],
  );

  const edges: Edge[] = useMemo(() => {
    const list: Edge[] = [];
    for (const [code, deps] of edgesIndex) {
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
            stroke: active ? "#1d4ed8" : "#c3ccd8",
            strokeWidth: active ? 2 : 1,
            opacity: selected !== null && !active ? 0.25 : 1,
          },
        });
      }
    }
    return list;
  }, [edgesIndex, selected, upstream, downstream]);

  const edgeCount = edgesIndex.size > 0 ? [...edgesIndex.values()].flat().length : 0;

  return (
    <section className="ml-graph" aria-label="指标依赖图谱">
      <div className="ml-graph__toolbar">
        <p className="ml-graph__hint">
          {visible.length} 个指标、{edgeCount} 条依赖边。
          点击节点查看上下游；颜色为能力域（{Object.values(domains).join(" / ")}）。
          支持缩放/平移/拖拽节点与 MiniMap 导航。
        </p>
        <label className="ml-graph__filter">
          分层{" "}
          <select
            aria-label="分层"
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value as typeof tierFilter)}
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
        className="ml-graph__flow"
        style={{ height: 560 }}
        role="region"
        aria-label="指标依赖关系有向图（可缩放平移）"
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.15, maxZoom: 1 }}
          minZoom={0.2}
          maxZoom={2}
          nodesDraggable
          nodesConnectable={false}
          proOptions={{ hideAttribution: true }}
          onNodeClick={(_event, node) => setSelected(node.id === selected ? null : node.id)}
        >
          <Background gap={24} color="#eef2f6" />
          <Controls showInteractive={false} />
          <MiniMap
            pannable
            zoomable
            nodeColor={(node) => (node.data as GraphNodeData).domainColor}
            nodeStrokeWidth={2}
          />
        </ReactFlow>
      </div>
      {layout.cyclic.length > 0 ? (
        <p className="ml-graph__warning" role="note">
          检测到依赖环（已按底层处理）：{layout.cyclic.join("、")}
        </p>
      ) : null}
      {selected ? (
        <p className="ml-graph__selected" role="status">
          已选中 <strong>{metrics.find((m) => m.metric_code === selected)?.name}</strong>
          （上游依赖 {upstream.size} 个、下游引用 {downstream.size} 个，蓝色高亮为直接关联链路）
        </p>
      ) : null}
    </section>
  );
}
