"use client";

// 指标依赖图谱（D040/D047 内部指标库 v1.1）：零依赖 SVG 确定性分层布局。
// 数据来自 GET /metric-library 的 depends_on；布局纯函数无随机性，快照可测。

import { useMemo, useState } from "react";
import type { MetricLibraryEntry } from "../../lib/api/client";

type Point = { x: number; y: number };

const NODE_W = 168;
const NODE_H = 46;
const COL_GAP = 84;
const ROW_GAP = 18;
const PADDING = 24;

type Layout = {
  layers: { code: string; entry: MetricLibraryEntry; x: number; y: number }[][];
  width: number;
  height: number;
  positions: Map<string, Point>;
};

/** 最长路径分层 + 层内按 code 排序；环依赖节点兜底到最后一层并标记 cyclic。 */
function computeLayout(metrics: MetricLibraryEntry[]): Layout & { cyclic: string[] } {
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

  const positions = new Map<string, Point>();
  const layers = buckets.map((codes, layer) =>
    codes.map((code, i) => {
      const x = PADDING + layer * (NODE_W + COL_GAP);
      const y = PADDING + i * (NODE_H + ROW_GAP);
      positions.set(code, { x, y });
      return { code, entry: byCode.get(code)!, x, y };
    }),
  );

  const width = PADDING * 2 + maxLayer * (NODE_W + COL_GAP) + NODE_W;
  const tallest = Math.max(...layers.map((l) => l.length));
  const graphHeight = PADDING * 2 + tallest * (NODE_H + ROW_GAP) - ROW_GAP;
  return { layers, width, height: Math.max(graphHeight, NODE_H + PADDING * 2), positions, cyclic };
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
  const edges = useMemo(
    () => new Map(visible.map((m) => [m.metric_code, (m.depends_on ?? []).filter((d) => layout.positions.has(d))])),
    [visible, layout],
  );

  const reverseIndex = useMemo(() => {
    const rev = new Map<string, string[]>();
    for (const [from, tos] of edges) {
      for (const to of tos) rev.set(to, [...(rev.get(to) ?? []), from]);
    }
    return rev;
  }, [edges]);
  const upstream = selected ? closure(edges, reverseIndex, selected, "up") : new Set<string>();
  const downstream = selected ? closure(edges, reverseIndex, selected, "down") : new Set<string>();

  const domainColor = (domain: string): string => {
    const palette: Record<string, string> = {
      solvency: "#1d4ed8", operation: "#0f766e", profitability: "#b45309",
      growth: "#7c3aed", cashflow: "#15803d", value: "#be185d", scale: "#475569",
    };
    return palette[domain] ?? "#475569";
  };

  const isDim = (code: string): boolean =>
    selected !== null && code !== selected && !upstream.has(code) && !downstream.has(code);

  return (
    <section className="ml-graph" aria-label="指标依赖图谱">
      <div className="ml-graph__toolbar">
        <p className="ml-graph__hint">
          {visible.length} 个指标、{[...edges.values()].flat().length} 条依赖边。
          点击节点查看上下游；颜色为能力域（
          {Object.values(domains).join(" / ")}）。
        </p>
        <label className="ml-graph__filter">
          分层{" "}
          <select
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

      <div className="ml-graph__scroll" tabIndex={0} role="region" aria-label="指标依赖关系图（可滚动）">
        <svg
          width={layout.width}
          height={layout.height}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="img"
          aria-label="指标依赖关系有向图，自左向右为从底层指标到复合指标"
        >
          {layout.layers.flatMap((nodes) =>
            nodes.map((node) =>
              (edges.get(node.code) ?? []).map((dep) => {
                const from = layout.positions.get(dep);
                if (!from) return null;
                const x1 = from.x + NODE_W;
                const y1 = from.y + NODE_H / 2;
                const x2 = node.x;
                const y2 = node.y + NODE_H / 2;
                const mid = (x1 + x2) / 2;
                const active =
                  selected !== null &&
                  (upstream.has(dep) || dep === selected) &&
                  (node.code === selected || downstream.has(node.code) || upstream.has(node.code));
                return (
                  <path
                    key={`${dep}->{node.code}`}
                    d={`M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`}
                    fill="none"
                    stroke={active ? "#1d4ed8" : "#c3ccd8"}
                    strokeWidth={active ? 2 : 1}
                    opacity={selected !== null && !active ? 0.25 : 1}
                  />
                );
              }),
            ),
          )}
          {layout.layers.map((nodes) =>
            nodes.map((node) => {
              const dim = isDim(node.code);
              const isSelected = node.code === selected;
              return (
                <g
                  key={node.code}
                  transform={`translate(${node.x}, ${node.y})`}
                  opacity={dim ? 0.3 : 1}
                  className="ml-graph__node"
                  onClick={() => setSelected(isSelected ? null : node.code)}
                  role="button"
                  aria-label={`${node.entry.name}（${node.entry.metric_code}）`}
                >
                  <title>
                    {node.entry.name} · {domains[node.entry.domain] ?? node.entry.domain}
                    {(node.entry.analysis_dimensions ?? []).length > 0
                      ? ` · 维度：${node.entry.analysis_dimensions.join(" / ")}`
                      : ""}
                  </title>
                  <rect
                    width={NODE_W}
                    height={NODE_H}
                    rx={8}
                    fill="#fff"
                    stroke={isSelected ? "#1d4ed8" : domainColor(node.entry.domain)}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                  />
                  <text x={10} y={19} className="ml-graph__node-name">
                    {node.entry.name.length > 10 ? `${node.entry.name.slice(0, 10)}…` : node.entry.name}
                  </text>
                  <text x={10} y={35} className="ml-graph__node-code">
                    {node.entry.metric_code.length > 20
                      ? `${node.entry.metric_code.slice(0, 20)}…`
                      : node.entry.metric_code}
                  </text>
                  {(node.entry.tier ?? "professional") === "core" ? (
                    <circle cx={NODE_W - 12} cy={12} r={4} fill="#f59e0b" aria-label="常用">
                      <title>常用指标</title>
                    </circle>
                  ) : null}
                </g>
              );
            }),
          )}
        </svg>
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
