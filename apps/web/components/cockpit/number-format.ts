export interface NumberFormatContext {
  metricCode?: string;
  unit?: string | null;
  appendUnit?: boolean;
}

const COUNT_METRICS = new Set([
  "orders",
  "china_orders_fulfilled",
  "international_parcels",
  "customer_count",
  "customers",
  "order_count",
  "parcel_count",
  "fulfillment_orders",
]);
const PERCENT_METRICS = new Set([
  "gross_margin",
  "roe",
  "net_margin",
  "debt_asset_ratio",
  "revenue_growth",
  "net_profit_growth",
  "operating_profit_growth",
  "fulfillment_cost_rate",
]);
const MULTIPLE_METRICS = new Set([
  "current_ratio",
  "quick_ratio",
  "cash_ratio",
  "inventory_turnover",
  "ar_turnover",
  "ap_turnover",
  "equity_multiplier",
  "total_asset_turnover",
  "interest_coverage",
  "debt_ebitda",
  "ocf_net_profit_ratio",
  "ocf_current_liab_ratio",
  "ocf_to_net_profit",
  "net_cash_ratio",
]);
const DAY_METRICS = new Set(["dso_days", "dio_days", "dpo_days", "ccc_days"]);

function numberFormat(minimumFractionDigits: number, maximumFractionDigits: number): Intl.NumberFormat {
  return new Intl.NumberFormat("zh-CN", {
    minimumFractionDigits,
    maximumFractionDigits,
    useGrouping: true,
  });
}

function normalizeRounded(value: number, maximumFractionDigits: number): number {
  const halfStep = 0.5 * 10 ** -maximumFractionDigits;
  return Math.abs(value) < halfStep ? 0 : value;
}

function formatRounded(value: number, minimumFractionDigits = 2, maximumFractionDigits = 2): string {
  return numberFormat(minimumFractionDigits, maximumFractionDigits).format(normalizeRounded(value, maximumFractionDigits));
}

function isMoneyUnit(unit: string): boolean {
  return /元|人民币|美元|港币|百万元|千元|CNY|USD|HKD|\$/.test(unit);
}

export function formatFinancialValue(
  raw: string | number | null | undefined,
  context: NumberFormatContext = {},
): string {
  if (raw === null || raw === undefined || raw === "") return "—";
  const value = typeof raw === "number" ? raw : Number(raw);
  if (!Number.isFinite(value)) return "—";

  const metricCode = context.metricCode ?? "";
  const unit = context.unit?.trim() ?? "";
  const unitSuffix = context.appendUnit === false || !unit ? "" : ` ${unit}`;

  if (MULTIPLE_METRICS.has(metricCode) || /倍|周转率/.test(unit)) {
    const suffix = /次/.test(unit) ? "次" : "倍";
    return `${formatRounded(value)}${context.appendUnit === false ? "" : ` ${suffix}`}`;
  }
  if (unit === "ratio" || PERCENT_METRICS.has(metricCode)) {
    const percent = unit === "ratio" || !unit ? value * 100 : value;
    return `${formatRounded(percent)}${context.appendUnit === false ? "" : "%"}`;
  }
  if (COUNT_METRICS.has(metricCode) || /^(单|件|票|客户|家|个|人)$/.test(unit)) {
    const countUnit = unit === "order" ? "单" : unit === "parcel" ? "件" : unit;
    const integer = Math.round(value);
    return `${numberFormat(0, 0).format(integer === 0 ? 0 : integer)}${context.appendUnit === false || !countUnit ? "" : ` ${countUnit}`}`;
  }
  if (DAY_METRICS.has(metricCode) || unit === "day") {
    return `${formatRounded(value, 0, 1)}${context.appendUnit === false ? "" : " 天"}`;
  }
  if (unit.includes("%")) {
    return `${formatRounded(value)}${context.appendUnit === false ? "" : "%"}`;
  }
  if (isMoneyUnit(unit)) {
    return `${formatRounded(value)}${unitSuffix}`;
  }

  return `${formatRounded(value)}${unitSuffix}`;
}

export function formatDeltaPercent(raw: string | number | null | undefined): string {
  if (raw === null || raw === undefined || raw === "") return "—";
  const value = typeof raw === "number" ? raw : Number(raw);
  if (!Number.isFinite(value)) return "—";
  const percent = value * 100;
  const normalized = normalizeRounded(percent, 2);
  return `${normalized > 0 ? "+" : ""}${formatRounded(normalized)}%`;
}
