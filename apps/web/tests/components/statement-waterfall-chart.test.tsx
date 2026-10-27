import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { WaterfallChart } from "../../components/statements/charts/waterfall-chart";
import { VISUAL_TOKENS } from "../../lib/visual-tokens.generated";

describe("WaterfallChart", () => {
  it("负利润时仍将负值柱与标签绘制在 SVG 画布内", () => {
    const { container } = render(
      <WaterfallChart
        items={[
          { label: "营业收入", value: 100, kind: "base" },
          { label: "经营成本", value: -130, kind: "delta" },
          { label: "净利润", value: -30, kind: "total" },
        ]}
        unitLabel="亿元"
        ariaLabel="负利润瀑布图"
      />,
    );

    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    const viewBoxHeight = Number(svg?.viewBox.baseVal.height);
    const bars = [...(svg?.querySelectorAll("rect") ?? [])];
    expect(bars).toHaveLength(3);
    expect(bars[0]?.getAttribute("fill")).toBe(VISUAL_TOKENS["colors-data-revenue"]);
    expect(bars[2]?.getAttribute("fill")).toBe(VISUAL_TOKENS["colors-semantic-negative"]);
    for (const bar of bars) {
      const bottom = Number(bar.getAttribute("y")) + Number(bar.getAttribute("height"));
      expect(bottom).toBeLessThanOrEqual(viewBoxHeight);
    }
    for (const label of [...(svg?.querySelectorAll("text") ?? [])]) {
      const y = Number(label.getAttribute("y"));
      expect(y).toBeGreaterThanOrEqual(0);
      expect(y).toBeLessThanOrEqual(viewBoxHeight);
    }
    const lines = [...(svg?.querySelectorAll("line") ?? [])];
    for (const line of lines) {
      for (const coordinate of ["y1", "y2"] as const) {
        const y = Number(line.getAttribute(coordinate));
        expect(y).toBeGreaterThanOrEqual(0);
        expect(y).toBeLessThanOrEqual(viewBoxHeight);
      }
    }
    expect(svg?.querySelector(".stmt-zero-line")).not.toBeNull();
  });

  it("仅有负总计时也将负柱完整保留在 SVG 画布内", () => {
    const { container } = render(
      <WaterfallChart
        items={[{ label: "期末现金", value: -30, kind: "total" }]}
        unitLabel="亿元"
        ariaLabel="负现金总计瀑布图"
      />,
    );

    const svg = container.querySelector("svg");
    expect(svg).not.toBeNull();
    const viewBoxHeight = Number(svg?.viewBox.baseVal.height);
    const bar = svg?.querySelector("rect");
    expect(bar).not.toBeNull();
    const bottom = Number(bar?.getAttribute("y")) + Number(bar?.getAttribute("height"));
    expect(bottom).toBeLessThanOrEqual(viewBoxHeight);
  });
});
