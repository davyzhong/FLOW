import { describe, expect, it } from "vitest";

import { formatDeltaPercent, formatFinancialValue } from "../components/cockpit/number-format";

describe("驾驶舱数字格式", () => {
  it("订单与包裹数量只显示整数", () => {
    expect(formatFinancialValue("12345.000000", { metricCode: "orders", unit: "单" })).toBe("12,345 单");
    expect(formatFinancialValue("1519.0000", { metricCode: "international_parcels", unit: "百万件" })).toBe("1,519 百万件");
    expect(formatFinancialValue("18191.4357", { metricCode: "orders", unit: "order" })).toBe("18,191 单");
  });

  it("金额统一显示两位小数并保留千分位", () => {
    expect(formatFinancialValue("71850.931000", { metricCode: "total_assets", unit: "百万元" })).toBe("71,850.93 百万元");
    expect(formatFinancialValue("-0.1", { metricCode: "cashflow", unit: "百万元" })).toBe("-0.10 百万元");
    expect(formatFinancialValue("-0.001", { metricCode: "cashflow", unit: "CNY" })).toBe("0.00 CNY");
  });

  it("appendUnit=false 仅输出格式化数值，供独立单位标签组合展示", () => {
    expect(formatFinancialValue("126895", { unit: "万元", appendUnit: false })).toBe("126,895.00");
    expect(formatFinancialValue("0.1087", { unit: "ratio", appendUnit: false })).toBe("10.87");
  });

  it("比例、倍数和天数遵循其业务单位", () => {
    expect(formatFinancialValue("0.6319", { metricCode: "debt_asset_ratio", unit: "ratio" })).toBe("63.19%");
    expect(formatFinancialValue("63.1900", { metricCode: "", unit: "%" })).toBe("63.19%");
    expect(formatFinancialValue("1000.0000", { metricCode: "orders", unit: "order" })).toBe("1,000 单");
    expect(formatFinancialValue("1.156", { metricCode: "current_ratio", unit: "倍" })).toBe("1.16 倍");
    expect(formatFinancialValue("1.156", { metricCode: "current_ratio", unit: "ratio" })).toBe("1.16 倍");
    expect(formatFinancialValue("1.156", { metricCode: "equity_multiplier", unit: "ratio" })).toBe("1.16 倍");
    expect(formatFinancialValue("0.8", { metricCode: "ocf_net_profit_ratio", unit: "ratio" })).toBe("0.80 倍");
    expect(formatFinancialValue("4.2", { metricCode: "debt_ebitda", unit: "ratio" })).toBe("4.20 倍");
    expect(formatFinancialValue("34.5000", { metricCode: "dso_days", unit: "day" })).toBe("34.5 天");
  });

  it("空值和非数值不伪装为零", () => {
    expect(formatFinancialValue(null, { metricCode: "orders", unit: "单" })).toBe("—");
    expect(formatFinancialValue("not-a-number", { metricCode: "orders", unit: "单" })).toBe("—");
  });

  it("将同比、环比等小数比率换算成百分比变化", () => {
    expect(formatDeltaPercent("0.061277")).toBe("+6.13%");
    expect(formatDeltaPercent("-0.308512")).toBe("-30.85%");
    expect(formatDeltaPercent("0")).toBe("0.00%");
    expect(formatDeltaPercent("-0.00001")).toBe("0.00%");
  });
});
