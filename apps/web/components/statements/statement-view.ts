// 报表分析视图层：typed API 数据 → 图形与表格数据。
// 所有换算只做单位缩放与挑行，不重算任何财务数字（D043 边界）。
import type {
  StatementLine,
  StatementReportDetail,
  StatementSection,
} from "../../lib/api/client";

export const YI_SCALE = 1e5; // 人民币千元 → 亿元

export function toNumber(value: string | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function toYi(value: string | null | undefined): number | null {
  const parsed = toNumber(value);
  return parsed === null ? null : parsed / YI_SCALE;
}

export function groupThousands(text: string): string {
  const [int, frac] = text.split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return frac ? `${grouped}.${frac}` : grouped;
}

export function formatYi(value: number, digits = 1): string {
  return groupThousands(value.toFixed(digits));
}

export function formatRaw(value: number): string {
  return groupThousands(value.toFixed(2).replace(/\.00$/, ""));
}

export function getSection(
  detail: StatementReportDetail,
  statementType: string,
): StatementSection | null {
  return detail.sections.find((section) => section.statement_type === statementType) ?? null;
}

function matchesAny(name: string, prefixes: string[]): boolean {
  return prefixes.some((prefix) => name.startsWith(prefix));
}

function pick(items: StatementLine[], prefixes: string[]): StatementLine | null {
  return items.find((line) => matchesAny(line.item_name, prefixes)) ?? null;
}

function pickValue(items: StatementLine[], prefixes: string[], column: ColumnKey): number | null {
  const line = pick(items, prefixes);
  if (!line) return null;
  return toYi(line[column]);
}

export type ColumnKey = "value_end" | "value_begin" | "value_current" | "value_prior";

const COLUMN_LABELS: Record<ColumnKey, string> = {
  value_end: "期末余额",
  value_begin: "期初余额",
  value_current: "本期发生额",
  value_prior: "上期发生额",
};

export function columnLayout(section: StatementSection): { key: ColumnKey; label: string }[] {
  const keys: ColumnKey[] = ["value_end", "value_begin", "value_current", "value_prior"];
  return keys
    .filter((key) => section.items.some((line) => line[key] !== null))
    .map((key) => ({ key, label: COLUMN_LABELS[key] }));
}

export type WaterfallItem = { label: string; value: number; kind: "base" | "delta" | "total" };

const BS = "合并资产负债表";
const IS = "合并利润表";
const CF = "合并现金流量表";

// 利润形成瀑布（本期）：收入 → 逐级扣减 → 净利润。任一关键行缺失返回 null，不伪造图形。
export function buildIncomeWaterfall(detail: StatementReportDetail): WaterfallItem[] | null {
  const items = getSection(detail, IS)?.items ?? [];
  const revenue = pickValue(items, ["一、营业总收入", "一、营业收入"], "value_current");
  const cost = pickValue(items, ["其中：营业成本", "二、营业总成本"], "value_current");
  const surcharge = pickValue(items, ["税金及附加"], "value_current");
  const selling = pickValue(items, ["销售费用"], "value_current");
  const admin = pickValue(items, ["管理费用"], "value_current");
  const research = pickValue(items, ["研发费用"], "value_current");
  const finance = pickValue(items, ["财务费用"], "value_current");
  const operating = pickValue(items, ["三、营业利润"], "value_current");
  const totalProfit = pickValue(items, ["四、利润总额"], "value_current");
  const tax = pickValue(items, ["减：所得税费用"], "value_current");
  const net = pickValue(items, ["五、净利润"], "value_current");
  if (
    revenue === null || cost === null || operating === null ||
    totalProfit === null || tax === null || net === null
  ) {
    return null;
  }
  const feeParts = [selling, admin, research, finance].filter((v): v is number => v !== null);
  const fees = feeParts.length ? feeParts.reduce((a, b) => a + b, 0) : null;
  const beforeOther = revenue - cost - (surcharge ?? 0) - (fees ?? 0);
  const otherOperating =
    feeParts.length && surcharge !== null
      ? Number((operating - beforeOther).toFixed(2))
      : null;
  const nonOperating = Number((totalProfit - operating).toFixed(2));
  const waterfall: WaterfallItem[] = [{ label: "营业总收入", value: revenue, kind: "base" }];
  waterfall.push({ label: "营业成本", value: -cost, kind: "delta" });
  if (surcharge !== null) waterfall.push({ label: "税金及附加", value: -surcharge, kind: "delta" });
  if (fees !== null) waterfall.push({ label: "期间费用", value: -fees, kind: "delta" });
  if (otherOperating !== null && Math.abs(otherOperating) >= 0.005) {
    waterfall.push({ label: "其他经营损益", value: otherOperating, kind: "delta" });
  }
  waterfall.push({ label: "营业利润", value: operating, kind: "total" });
  if (nonOperating !== 0) {
    waterfall.push({ label: "营业外净收支", value: nonOperating, kind: "delta" });
  }
  waterfall.push({ label: "所得税费用", value: -tax, kind: "delta" });
  waterfall.push({ label: "净利润", value: net, kind: "total" });
  return waterfall;
}

export type KpiItem = { label: string; display: string; exact: string | null };

const AGGREGATE_EXCLUSION = /合计|小计|^其中|以“－”号填列）$/;

export function buildKpis(detail: StatementReportDetail): KpiItem[] {
  const isItems = getSection(detail, IS)?.items ?? [];
  const cfItems = getSection(detail, CF)?.items ?? [];
  const bsItems = getSection(detail, BS)?.items ?? [];
  const kpis: KpiItem[] = [];
  const push = (label: string, value: number | null, exact: string | null, suffix = "亿元") => {
    if (value === null) return;
    kpis.push({ label, display: `${formatYi(value, 2)} ${suffix}`, exact });
  };
  const revenue = pickValue(isItems, ["一、营业总收入", "一、营业收入"], "value_current");
  const net = pickValue(isItems, ["五、净利润"], "value_current");
  const attributable = pickValue(
    isItems,
    ["1.归属于母公司所有者的净利润", "1.归属于母公司股东的净利润"],
    "value_current",
  );
  const operating = pickValue(cfItems, ["经营活动产生的现金流量净额"], "value_current");
  const assets = pickValue(bsItems, ["资产总计"], "value_end");
  push("营业总收入", revenue, findExact(isItems, ["一、营业总收入", "一、营业收入"], "value_current"));
  push("净利润", net, findExact(isItems, ["五、净利润"], "value_current"));
  push("归母净利润", attributable, findExact(
    isItems,
    ["1.归属于母公司所有者的净利润", "1.归属于母公司股东的净利润"],
    "value_current",
  ));
  push("经营活动现金流净额", operating, findExact(cfItems, ["经营活动产生的现金流量净额"], "value_current"));
  push("资产总计", assets, findExact(bsItems, ["资产总计"], "value_end"));
  const eps = pick(isItems, ["（一）基本每股收益"]);
  if (eps) {
    const raw = toNumber(eps.value_current);
    if (raw !== null) kpis.push({ label: "基本每股收益", display: `${raw.toFixed(2)} 元`, exact: eps.value_current ?? null });
  }
  if (revenue !== null && net !== null) {
    kpis.push({
      label: "净利率",
      display: `${((net / revenue) * 100).toFixed(2)}%`,
      exact: null,
    });
  }
  return kpis.filter((item) => !AGGREGATE_EXCLUSION.test(item.label));
}

function findExact(items: StatementLine[], prefixes: string[], column: ColumnKey): string | null {
  const line = pick(items, prefixes);
  if (!line) return null;
  return line[column] ?? null;
}

export type DonutItem = { label: string; value: number };

export function buildAssetDonut(detail: StatementReportDetail): DonutItem[] | null {
  const items = getSection(detail, BS)?.items ?? [];
  const total = pickValue(items, ["资产总计"], "value_end");
  if (total === null) return null;
  const parts = items
    .filter((line) => line.value_end !== null)
    .filter((line) => !/合计|小计|^其中|：$/.test(line.item_name))
    .map((line) => ({ label: line.item_name, value: toYi(line.value_end) ?? 0 }))
    .filter((part) => part.value > 0)
    .sort((a, b) => b.value - a.value);
  if (!parts.length) return null;
  const top = parts.slice(0, 6);
  const rest = Number((total - top.reduce((sum, part) => sum + part.value, 0)).toFixed(2));
  const donut = top.map((part) => ({ label: part.label, value: Number(part.value.toFixed(2)) }));
  if (Math.abs(rest) >= 0.01) donut.push({ label: "其他科目", value: rest });
  return donut;
}

export function buildCapitalDonut(detail: StatementReportDetail): DonutItem[] | null {
  const items = getSection(detail, BS)?.items ?? [];
  const current = pickValue(items, ["流动负债合计"], "value_end");
  const equity = pickValue(items, ["所有者权益"], "value_end");
  if (current === null || equity === null) return null;
  const nonCurrent =
    pickValue(items, ["非流动负债合计"], "value_end") ??
    (() => {
      const totalLiab = pickValue(items, ["负债合计"], "value_end");
      return totalLiab === null ? null : Number((totalLiab - current).toFixed(2));
    })();
  if (nonCurrent === null) return null;
  return [
    { label: "流动负债", value: Number(current.toFixed(2)) },
    { label: "非流动负债", value: Number(nonCurrent.toFixed(2)) },
    { label: "所有者权益", value: Number(equity.toFixed(2)) },
  ];
}

export type CashflowBar = {
  label: string;
  current: number;
  prior: number | null;
};

export function buildCashflowBars(detail: StatementReportDetail): CashflowBar[] | null {
  const items = getSection(detail, CF)?.items ?? [];
  const defs: { label: string; prefixes: string[] }[] = [
    { label: "经营活动净额", prefixes: ["经营活动产生的现金流量净额"] },
    { label: "投资活动净额", prefixes: ["投资活动产生的现金流量净额"] },
    { label: "筹资活动净额", prefixes: ["筹资活动产生的现金流量净额"] },
  ];
  const bars = defs.map((def) => ({
    label: def.label,
    current: pickValue(items, def.prefixes, "value_current"),
    prior: pickValue(items, def.prefixes, "value_prior"),
  }));
  const defined = bars.filter(
    (bar): bar is { label: string; current: number; prior: number | null } => bar.current !== null,
  );
  return defined.length ? defined : null;
}

export function buildCashBridge(detail: StatementReportDetail): WaterfallItem[] | null {
  const items = getSection(detail, CF)?.items ?? [];
  const opening = pickValue(
    items,
    ["加：期初现金及现金等价物余额", "期初现金及现金等价物余额"],
    "value_current",
  );
  const closing = pickValue(
    items,
    ["六、期末现金及现金等价物余额", "期末现金及现金等价物余额"],
    "value_current",
  );
  if (opening === null || closing === null) return null;
  const operating = pickValue(items, ["经营活动产生的现金流量净额"], "value_current");
  const investing = pickValue(items, ["投资活动产生的现金流量净额"], "value_current");
  const financing = pickValue(items, ["筹资活动产生的现金流量净额"], "value_current");
  const fx = pickValue(items, ["四、汇率变动对现金及现金等价物的影响"], "value_current");
  const bridge: WaterfallItem[] = [{ label: "期初现金", value: opening, kind: "base" }];
  for (const part of [
    { label: "经营活动", value: operating },
    { label: "投资活动", value: investing },
    { label: "筹资活动", value: financing },
    { label: "汇率影响", value: fx },
  ]) {
    if (part.value !== null) {
      bridge.push({ label: part.label, value: part.value, kind: "delta" });
    }
  }
  bridge.push({ label: "期末现金", value: closing, kind: "total" });
  return bridge;
}

export function hasStatement(detail: StatementReportDetail, statementType: string): boolean {
  return detail.sections.some((section) => section.statement_type === statementType);
}
