import { describe, expect, it } from "vitest";

import {
  dashboardFilterHref,
  dataBatchHref,
  metricAnchorId,
  metricEntryHref,
  metricFocusHref,
  operationsReportHref,
  reportsFocusHref,
  reportsSnapshotHref,
  statementReportHref,
  statementRowId,
} from "../lib/deep-links";

describe("deep-link href builders", () => {
  it("builds receiver hrefs matching the batch-1 parameter contract", () => {
    expect(metricFocusHref("gross_margin")).toBe("/metric-library?focus=gross_margin");
    expect(metricEntryHref("entry-1")).toBe("/metric-library?entry=entry-1");
    expect(statementReportHref("r-1")).toBe("/statements?report=r-1");
    expect(reportsSnapshotHref("snap-1")).toBe("/reports?snapshot=snap-1");
    expect(reportsFocusHref("ms-1")).toBe("/reports?focus=ms-1");
    expect(dataBatchHref("b-1")).toBe("/data?batch=b-1");
    expect(operationsReportHref("r-1")).toBe("/operations?report=r-1");
  });

  it("encodes reserved characters in parameter values", () => {
    expect(metricFocusHref("a b&c")).toBe("/metric-library?focus=a%20b%26c");
  });

  it("builds dashboard filter hrefs with only the four dimension keys", () => {
    expect(dashboardFilterHref({ logistics_product_id: "p1" })).toBe("/?logistics_product_id=p1");
    expect(
      dashboardFilterHref({ customer_segment_id: "c1", logistics_product_id: "p1" }),
    ).toBe("/?customer_segment_id=c1&logistics_product_id=p1");
    expect(dashboardFilterHref({})).toBe("/");
  });

  it("anchors metric cards by entry_id first, then collection + code", () => {
    expect(metricAnchorId({ metric_code: "gross_margin", entry_id: "e-1", collection: "general" }))
      .toBe("metric-entry-e-1");
    expect(metricAnchorId({ metric_code: "gross_margin", collection: "logistics" }))
      .toBe("metric-logistics-gross_margin");
    expect(metricAnchorId({ metric_code: "gross_margin" })).toBe("metric-general-gross_margin");
  });

  it("derives whitespace-free statement row ids for in-page anchors", () => {
    expect(statementRowId("合并利润表", "一、营业总收入")).toBe("stmt-row-合并利润表-一、营业总收入");
    expect(statementRowId("合并 利润表", "货币 资金")).toBe("stmt-row-合并_利润表-货币_资金");
  });
});
