import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "../app/page";

describe("FLOW home", () => {
  it("identifies the Finance BP workspace", () => {
    render(<HomePage />);

    expect(screen.getByRole("heading", { name: "FLOW" })).toBeVisible();
    expect(screen.getByText("Finance BP 经营分析工作台")).toBeVisible();
  });
});
