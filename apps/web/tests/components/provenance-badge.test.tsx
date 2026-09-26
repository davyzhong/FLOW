import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProvenanceBadge } from "../../components/ui/provenance-badge";

// FE-08 可达性切片：溯源徽标必须可点击展开（触屏路径）、Escape 关闭、
// 点击外部关闭；无页码定位时渲染占位而不伪造溯源。

describe("ProvenanceBadge", () => {
  it("renders an em dash placeholder without page anchor", () => {
    render(<ProvenanceBadge page={null} anchor={null} />);
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("toggles the provenance card via click with aria-expanded", () => {
    render(<ProvenanceBadge page={12} anchor="strong" sourceRef="docs/x.pdf" />);
    const button = screen.getByRole("button", { name: /溯源：原文第 12 页/ });
    expect(button).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(/锚定方式：行名\+数值同页/)).toBeInTheDocument();
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on Escape", () => {
    render(<ProvenanceBadge page={3} anchor="weak" />);
    const button = screen.getByRole("button", { name: /溯源：原文第 3 页/ });
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-expanded", "true");
    fireEvent.keyDown(button, { key: "Escape" });
    expect(button).toHaveAttribute("aria-expanded", "false");
  });

  it("closes on outside pointer down", () => {
    render(
      <div>
        <ProvenanceBadge page={7} anchor="strong" />
        <button type="button">外部按钮</button>
      </div>,
    );
    const badge = screen.getByRole("button", { name: /溯源：原文第 7 页/ });
    fireEvent.click(badge);
    expect(badge).toHaveAttribute("aria-expanded", "true");
    fireEvent.pointerDown(screen.getByRole("button", { name: "外部按钮" }));
    expect(badge).toHaveAttribute("aria-expanded", "false");
  });

  it("links to a registered source PDF at the exact source page", () => {
    render(
      <ProvenanceBadge
        page={17}
        anchor="strong"
        sourceSha256={"a".repeat(64)}
        sourceAvailable
      />,
    );
    expect(screen.getAllByRole("link", { name: /打开原文 PDF 第 17 页/ })[0]).toHaveAttribute(
      "href",
      `/api/v1/statements/sources/${"a".repeat(64)}/content#page=17`,
    );
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("does not offer a raw PDF link when the source is not registered", () => {
    render(
      <ProvenanceBadge
        page={17}
        anchor="strong"
        sourceSha256={"a".repeat(64)}
        sourceAvailable={false}
      />,
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /溯源：原文第 17 页/ })).toBeInTheDocument();
  });
});
