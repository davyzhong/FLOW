import { expect, test } from "@playwright/test";

async function openInvestigation(page: import("@playwright/test").Page) {
  await page.goto("/");
  await expect(page.getByTestId("metric-card")).toHaveCount(8);
  await page.getByRole("link", { name: /履约成本增加：进入调查/ }).click();
  const receipt = page.getByRole("region", { name: "不可变分析上下文" });
  await expect(receipt).toContainText("Finding ID");
  await expect(receipt).toContainText("数据批次 ID");
  await expect(receipt).toContainText("指标快照 ID");
  await expect(receipt).toContainText("分析运行 ID");
  await expect(page.getByRole("region", { name: "驱动计算明细" })).toBeVisible();
  await expect(page.getByRole("region", { name: "关键源记录" })).toContainText(/!R\d+/);
}

async function fillConclusion(page: import("@playwright/test").Page) {
  const panel = page.getByRole("region", { name: "结构化结论" });
  await panel.getByLabel("已验证事实").fill("履约成本率同比上升，运输单价上涨为最大贡献。");
  await panel.getByLabel("分析判断").fill("成本上升主要来自外包运输涨价，而非业务量不足。");
  await panel.getByLabel("仍待确认").fill("两家承运商的新报价审批单尚未归档。");
  await panel.getByLabel("管理建议").fill("对 Top 3 承运商重新议价并复核运输结构。");
  await panel.getByRole("button", { name: "保存结论" }).click();
  await expect(panel.getByRole("button", { name: "已保存 ✓" })).toBeVisible();
}

test("finance BP reproduces finding context and records a governed conclusion", async ({
  page,
}) => {
  await openInvestigation(page);

  await expect(page.getByTestId("finding-status")).toHaveText("待提交");
  await fillConclusion(page);
});

test("rejected evidence blocks approval until re-verified, then finding is approved", async ({
  page,
}) => {
  await openInvestigation(page);

  await fillConclusion(page);
  await expect(page.getByTestId("finding-status")).toHaveText("复核中");

  const inspector = page.getByRole("region", { name: "证据复核" });
  await inspector.getByRole("button", { name: "否定" }).first().click();
  await expect(page.getByRole("region", { name: "口径与数据检查" })).toContainText(
    "存在被否定证据",
  );

  await page.getByRole("button", { name: "批准签发" }).click();
  await expect(page.locator(".investigation-action-error")).toContainText(
    "存在被否定证据",
  );

  await inspector.getByRole("button", { name: "确认此证据" }).first().click();
  await page.getByRole("button", { name: "批准签发" }).click();
  await expect(page.getByTestId("finding-status")).toHaveText("已签发");
  await expect(page.getByRole("region", { name: "口径与数据检查" })).toContainText(
    "具备报告资格",
  );

  const history = page.getByRole("region", { name: "审阅操作" });
  await expect(history).toContainText("批准签发");
});
