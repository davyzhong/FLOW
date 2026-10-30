import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GroupedBarChart } from "../../components/statements/charts/grouped-bar-chart";
import { VISUAL_TOKENS } from "../../lib/visual-tokens.generated";

describe("GroupedBarChart", () => {
  it("现金流净额为负时仍用期间色区分，符号由零轴和数值表达", () => {
    const { container } = render(
      <GroupedBarChart
        items={[{ label: "投资活动净额", current: -20, prior: -12 }]}
        currentLabel="本期"
        priorLabel="上期"
        unitLabel="亿元"
        ariaLabel="现金流量三活动净额"
      />,
    );
    const bars = [...container.querySelectorAll("g > g > rect")];
    expect(bars.map((bar) => bar.getAttribute("fill"))).toEqual([
      VISUAL_TOKENS["colors-data-revenue"],
      VISUAL_TOKENS["colors-data-series4"],
    ]);
    expect(container.textContent).toContain("-20");
  });
});
