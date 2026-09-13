// 报表分析视图层：typed API 数据 → 图形与表格数据。
// 所有换算只做单位缩放与挑行，不重算任何财务数字（D043 边界）。
import type {
  StatementLine,
  StatementReportDetail,
  StatementSection,
} from "../../lib/api/client";

export const YI_SCALE = 1e5; // 人民币千元 → 亿元

// 披露单位 → 亿元的缩放因子：千元 1e5、百万元 1e2、亿元 1。
// 单位只从 unit_note 读取；读不到时按历史默认（千元）处理，不猜测。
export function yiScale(unitNote: string | null | undefined): number {
  if (!unitNote) return YI_SCALE;
  if (unitNote.includes("千元")) return 1e5;
  if (unitNote.includes("百万")) return 1e2;
  if (unitNote.includes("亿元")) return 1;
  return YI_SCALE;
}

export function toNumber(value: string | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

export function toYi(value: string | null | undefined, scale: number = YI_SCALE): number | null {
  const parsed = toNumber(value);
  return parsed === null ? null : parsed / scale;
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

// 先精确匹配、再前缀匹配：避免「收入」误中「收入成本」这类前缀重叠行。
function pick(items: StatementLine[], prefixes: string[]): StatementLine | null {
  for (const prefix of prefixes) {
    const exact = items.find((line) => line.item_name === prefix);
    if (exact) return exact;
  }
  return items.find((line) => matchesAny(line.item_name, prefixes)) ?? null;
}

function pickValue(
  items: StatementLine[],
  prefixes: string[],
  column: ColumnKey,
  scale: number = YI_SCALE,
): number | null {
  const line = pick(items, prefixes);
  if (!line) return null;
  return toYi(line[column], scale);
}

// 资产负债表期末值：部分抽取器（如菜鸟申报稿）把余额列存为 本期发生额/上期发生额，
// 期末取值回退到 value_current，期初回退到 value_prior，语义由抽取产物定义。
function endScaled(line: StatementLine, scale: number): number | null {
  return toYi(line.value_end ?? line.value_current, scale);
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

// 披露行项目命名：CAS（顺丰）与 IFRS（腾讯/京东物流/阿里巴巴/菜鸟）两套。
const CAS_REVENUE = ["一、营业总收入", "一、营业收入"];
const IFRS_REVENUE = ["收入"];
const CAS_COST = ["其中：营业成本", "二、营业总成本"];
const IFRS_COST = ["營業成本", "营业成本", "收入成本"];
const GROSS_PROFIT = ["毛利"];
const CAS_OPERATING = ["三、营业利润"];
const IFRS_OPERATING = ["經營利潤", "经营盈利", "經營盈利", "经营亏损/利润", "经营利润"];
const CAS_PRETAX = ["四、利润总额"];
const IFRS_PRETAX = [
  "扣除所得稅及權益法核算的投資損益前的利潤",
  "除税前盈利",
  "除税前亏损/利润",
  "除稅前利潤",
  "除税前利润",
];
const CAS_TAX = ["减：所得税费用"];
const IFRS_TAX = ["所得稅費用", "所得税开支", "所得稅開支", "所得税费用"];
const CAS_NET = ["五、净利润"];
const IFRS_NET = ["年度利润", "年度利潤", "年度溢利", "期内盈利", "期內盈利", "淨利潤", "年度亏损/利润"];
const IFRS_FEES = [
  "產品開發費用",
  "銷售和市場費用",
  "一般及行政費用",
  "無形資產攤銷及減值",
  "商譽減值",
  "销售及市场推广开支",
  "銷售及市場推廣開支",
  "一般及行政开支",
  "一般及行政開支",
  "产品开发开支",
  "研發開支",
  "金融资产减值(转回)/计提",
  "金融資產減值損失（包括減值損失轉回）",
];
const OPERATING_CF = [
  "经营活动产生的现金流量净额",
  "經營活動產生的現金流量淨額",
  "经营活动所得现金净额",
  "經營活動所得現金淨額",
];
const INVESTING_CF = [
  "投资活动产生的现金流量净额",
  "投資活動產生的現金流量淨額",
  "投资活动所用现金净额",
  "投資活動所用現金流量淨額",
  "投資活動所用現金淨額",
];
const FINANCING_CF = [
  "筹资活动产生的现金流量净额",
  "融資活動產生的現金流量淨額",
  "融资活动(所用)所得现金净额",
  "融資活動所用現金流量淨額",
  "融資活動所用現金淨額",
];
const TOTAL_ASSETS = ["资产总计", "資產總額", "资产总额"];
const ATTRIBUTABLE_NET = [
  "1.归属于母公司所有者的净利润",
  "1.归属于母公司股东的净利润",
  "歸屬於阿里巴巴集團股東的淨利潤",
  "本公司权益持有人",
  "本公司權益持有人",
  "本公司所有者",
  "归属公司所有者",
];
// 减值类费用行在 IFRS 报表中可能为负数（转回），瀑布里按披露符号原样扣减。
function neg(value: number): number {
  return value > 0 ? -value : value;
}

// 利润形成瀑布（本期）：收入 → 逐级扣减 → 净利润。任一关键行缺失返回 null，不伪造图形。
export function buildIncomeWaterfall(detail: StatementReportDetail): WaterfallItem[] | null {
  const scale = yiScale(detail.unit_note);
  const items = getSection(detail, IS)?.items ?? [];
  const casRevenue = pickValue(items, CAS_REVENUE, "value_current", scale);
  if (casRevenue === null) return buildIfrsWaterfall(items, scale);
  const revenue = casRevenue;
  const cost = pickValue(items, CAS_COST, "value_current", scale);
  const surcharge = pickValue(items, ["税金及附加"], "value_current", scale);
  const selling = pickValue(items, ["销售费用"], "value_current", scale);
  const admin = pickValue(items, ["管理费用"], "value_current", scale);
  const research = pickValue(items, ["研发费用"], "value_current", scale);
  const finance = pickValue(items, ["财务费用"], "value_current", scale);
  const operating = pickValue(items, CAS_OPERATING, "value_current", scale);
  const totalProfit = pickValue(items, CAS_PRETAX, "value_current", scale);
  const tax = pickValue(items, CAS_TAX, "value_current", scale);
  const net = pickValue(items, CAS_NET, "value_current", scale);
  if (
    cost === null || operating === null ||
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

// IFRS 利润瀑布（腾讯/阿里巴巴/菜鸟等港股披露结构）：
// 收入 → 营业成本 →（毛利）→ 费用合计 → 其他经营损益（残差，显式）→ 经营利润
// → 除税前调整（残差，显式）→ 除税前利润 → 所得税 → 净利润。
function buildIfrsWaterfall(items: StatementLine[], scale: number): WaterfallItem[] | null {
  const revenue = pickValue(items, IFRS_REVENUE, "value_current", scale);
  const cost = pickValue(items, IFRS_COST, "value_current", scale);
  const gross = pickValue(items, GROSS_PROFIT, "value_current", scale);
  const operating = pickValue(items, IFRS_OPERATING, "value_current", scale);
  const pretax = pickValue(items, IFRS_PRETAX, "value_current", scale);
  const tax = pickValue(items, IFRS_TAX, "value_current", scale);
  const net = pickValue(items, IFRS_NET, "value_current", scale);
  if (
    revenue === null || cost === null || operating === null ||
    pretax === null || tax === null || net === null
  ) {
    return null;
  }
  const feeParts = IFRS_FEES.map((prefix) =>
    pickValue(items, [prefix], "value_current", scale),
  ).filter((v): v is number => v !== null);
  const fees = feeParts.length ? feeParts.reduce((a, b) => a + b, 0) : 0;
  const base = revenue + neg(cost) + (feeParts.length ? neg(fees) : 0);
  const otherOperating = Number((operating - base).toFixed(2));
  const pretaxAdjust = Number((pretax - operating).toFixed(2));
  const waterfall: WaterfallItem[] = [{ label: "收入", value: revenue, kind: "base" }];
  waterfall.push({ label: "营业成本", value: neg(cost), kind: "delta" });
  if (gross !== null) waterfall.push({ label: "毛利", value: gross, kind: "total" });
  if (feeParts.length) waterfall.push({ label: "费用合计", value: neg(fees), kind: "delta" });
  if (Math.abs(otherOperating) >= 0.005) {
    waterfall.push({ label: "其他经营损益", value: otherOperating, kind: "delta" });
  }
  waterfall.push({ label: "经营利润", value: operating, kind: "total" });
  if (Math.abs(pretaxAdjust) >= 0.005) {
    waterfall.push({ label: "除税前调整", value: pretaxAdjust, kind: "delta" });
  }
  waterfall.push({ label: "除税前利润", value: pretax, kind: "total" });
  waterfall.push({ label: "所得税", value: neg(tax), kind: "delta" });
  // 部分披露（如阿里巴巴）在所得税之后还有权益法投资损益；其余公司该行为空。
  const equityPickup = pickValue(
    items,
    ["權益法核算的投資損益", "权益法核算的投资损益"],
    "value_current",
    scale,
  );
  if (equityPickup !== null && Math.abs(equityPickup) >= 0.005) {
    waterfall.push({ label: "权益法投资损益", value: equityPickup, kind: "delta" });
  }
  // 税后残差显式呈现，保证瀑布闭合到披露净利润，不吞差。
  const tailResidual = Number(
    (net - (pretax + neg(tax) + (equityPickup ?? 0))).toFixed(2),
  );
  if (Math.abs(tailResidual) >= 0.005) {
    waterfall.push({ label: "其他税后损益", value: tailResidual, kind: "delta" });
  }
  waterfall.push({ label: "净利润", value: net, kind: "total" });
  return waterfall;
}

export type KpiItem = { label: string; display: string; exact: string | null };

const AGGREGATE_EXCLUSION = /合计|小计|^其中|以“－”号填列）$/;

export function buildKpis(detail: StatementReportDetail): KpiItem[] {
  const scale = yiScale(detail.unit_note);
  const isItems = getSection(detail, IS)?.items ?? [];
  const cfItems = getSection(detail, CF)?.items ?? [];
  const bsItems = getSection(detail, BS)?.items ?? [];
  const kpis: KpiItem[] = [];
  const push = (label: string, value: number | null, exact: string | null, suffix = "亿元") => {
    if (value === null) return;
    kpis.push({ label, display: `${formatYi(value, 2)} ${suffix}`, exact });
  };
  const revenueLine = pick(isItems, [...CAS_REVENUE, ...IFRS_REVENUE]);
  const netLine = pick(isItems, [...CAS_NET, ...IFRS_NET]);
  const attributableLine = pick(isItems, ATTRIBUTABLE_NET);
  const operatingLine = pick(cfItems, OPERATING_CF);
  const assetsLine = pick(bsItems, TOTAL_ASSETS);
  const revenue = revenueLine ? toYi(revenueLine.value_current, scale) : null;
  const net = netLine ? toYi(netLine.value_current, scale) : null;
  const attributable = attributableLine ? toYi(attributableLine.value_current, scale) : null;
  const operating = operatingLine ? toYi(operatingLine.value_current, scale) : null;
  const assets = assetsLine ? endScaled(assetsLine, scale) : null;
  const isCas = pick(isItems, CAS_REVENUE) !== null;
  // CAS 用固定短标签；IFRS 直接用披露行名（收入/年度利潤/期内盈利…）。
  push(isCas ? "营业总收入" : (revenueLine?.item_name ?? "收入"), revenue, revenueLine?.value_current ?? null);
  push(isCas ? "净利润" : (netLine?.item_name ?? "净利润"), net, netLine?.value_current ?? null);
  push(isCas ? "归母净利润" : (attributableLine?.item_name ?? "归母净利润"), attributable, attributableLine?.value_current ?? null);
  push(isCas ? "经营活动现金流净额" : (operatingLine?.item_name ?? "经营现金流净额"), operating, operatingLine?.value_current ?? null);
  push(isCas ? "资产总计" : (assetsLine?.item_name ?? "资产总计"), assets, (assetsLine ? (assetsLine.value_end ?? assetsLine.value_current) : null) ?? null);
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

export type DonutItem = { label: string; value: number };

// 资产构成环形图只取资产行。两个截断点取孰早：
// 1) 资产总计行（CAS/阿里/京东物流的合计行在清单中段）；
// 2) 第一个负债/权益类科目（菜鸟申报稿的合计行在清单末尾，负债与权益行紧随资产之后）。
const LIABILITY_EQUITY_START =
  /^(短期借款|长期借款|借款|租赁负债|租賃負債|应付|應付|预收|預收|预提|預提|合同负债|合同負債|递延收益|递延收入|遞延收入|递延税项负债|遞延稅項負債|本期税项负债|应交税费|應交稅費|其他应付款|其他應付款|长期应付款|長期應付款|其他金融负债|指定按公允价值计量的金融负债|应付合并|應付合併|股本|普通股|库存股|庫存股|资本公积|資本公積|股份溢价|其他储备|其他儲備|法定储备|法定儲備|留存收益|未分配利润|累计亏损|累計虧損|累计其他综合收益|累計其他綜合收益|夹层权益|夾層權益|归属于|歸屬於|非控制性权益|非控制性權益|少数股东权益|少數股東權益|所有者权益|股東權益|股东权益|權益總額|权益总额)/;

export function buildAssetDonut(detail: StatementReportDetail): DonutItem[] | null {
  const scale = yiScale(detail.unit_note);
  const items = getSection(detail, BS)?.items ?? [];
  const totalLine = pick(items, TOTAL_ASSETS);
  if (!totalLine) return null;
  const total = endScaled(totalLine, scale);
  if (total === null) return null;
  const totalIndex = items.indexOf(totalLine);
  const liabilityIndex = items.findIndex((line) => LIABILITY_EQUITY_START.test(line.item_name));
  const cutIndex =
    liabilityIndex >= 0 ? Math.min(totalIndex, liabilityIndex) : totalIndex;
  const assetRows = items.slice(0, cutIndex);
  const parts = assetRows
    .filter((line) => (line.value_end ?? line.value_current) !== null)
    .filter((line) => !/合计|小计|總額|总额|^其中|：$/.test(line.item_name))
    .map((line) => ({ label: line.item_name, value: endScaled(line, scale) ?? 0 }))
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
  const scale = yiScale(detail.unit_note);
  const items = getSection(detail, BS)?.items ?? [];
  const currentLine = pick(items, ["流动负债合计", "流動負債總額", "流动负债总额"]);
  const equityLine = pick(items, ["所有者权益", "權益總額", "权益总额", "股東權益總額"]);
  const current = currentLine ? endScaled(currentLine, scale) : null;
  const equity = equityLine ? endScaled(equityLine, scale) : null;
  if (current === null || equity === null) return null;
  const nonCurrentLine = pick(items, ["非流动负债合计", "非流動負債總額", "非流动负债总额"]);
  const nonCurrent =
    (nonCurrentLine ? endScaled(nonCurrentLine, scale) : null) ??
    (() => {
      const totalLine = pick(items, ["负债合计", "負債總額", "负债总额"]);
      const totalLiab = totalLine ? endScaled(totalLine, scale) : null;
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
  const scale = yiScale(detail.unit_note);
  const items = getSection(detail, CF)?.items ?? [];
  const defs: { label: string; prefixes: string[] }[] = [
    { label: "经营活动净额", prefixes: OPERATING_CF },
    { label: "投资活动净额", prefixes: INVESTING_CF },
    { label: "筹资活动净额", prefixes: FINANCING_CF },
  ];
  const bars = defs.map((def) => ({
    label: def.label,
    current: pickValue(items, def.prefixes, "value_current", scale),
    prior: pickValue(items, def.prefixes, "value_prior", scale),
  }));
  const defined = bars.filter(
    (bar): bar is { label: string; current: number; prior: number | null } => bar.current !== null,
  );
  return defined.length ? defined : null;
}

export function buildCashBridge(detail: StatementReportDetail): WaterfallItem[] | null {
  const scale = yiScale(detail.unit_note);
  const items = getSection(detail, CF)?.items ?? [];
  const opening = pickValue(
    items,
    [
      "加：期初现金及现金等价物余额",
      "期初现金及现金等价物余额",
      "期初現金及現金等價物",
      "年初现金及现金等价物",
      "年初現金及現金等價物",
    ],
    "value_current",
    scale,
  );
  const closing = pickValue(
    items,
    [
      "六、期末现金及现金等价物余额",
      "期末现金及现金等价物余额",
      "期末現金及現金等價物",
      "年末现金及现金等价物",
      "年末現金及現金等價物",
    ],
    "value_current",
    scale,
  );
  if (opening === null || closing === null) return null;
  const operating = pickValue(items, OPERATING_CF, "value_current", scale);
  const investing = pickValue(items, INVESTING_CF, "value_current", scale);
  const financing = pickValue(items, FINANCING_CF, "value_current", scale);
  const fx = pickValue(
    items,
    [
      "四、汇率变动对现金及现金等价物的影响",
      "匯率變動對現金的影響",
      "汇率变动对现金的影响",
      "外匯匯率變動對現金及現金等價物的影響",
    ],
    "value_current",
    scale,
  );
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
