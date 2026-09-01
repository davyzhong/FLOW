import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "../app/page";

describe("FLOW home", () => {
  it("identifies the Finance BP workspace", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { name: "Finance BP 经营驾驶舱" }),
    ).toBeVisible();
    expect(screen.getByText("FLOW · FINANCE INTELLIGENCE")).toBeVisible();
  });
});
