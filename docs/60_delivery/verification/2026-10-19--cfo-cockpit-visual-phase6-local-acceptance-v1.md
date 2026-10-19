---
doc_id: FLOW-VER-COCKPIT-VISUAL-PHASE6-20261019-001
title: CFO 驾驶舱概念板视觉升级阶段六本机验收
doc_type: verification
status: verified
version: 1.0
created_at: 2026-10-19
updated_at: 2026-10-19
owner: FLOW
commit_refs: [e1fa91cbce5997f306479cdcb5344d1587c57369]
evidence_refs: [web-vitest-196, web-build, web-lint, damai-isolated-e2e-9-routes-2-viewports, cockpit-visual-screenshots-20261019, github-run-39265415539, isolated-data-contract-dc705]
applies_to: repository
---

# CFO 驾驶舱概念板视觉升级阶段六本机验收

## 结论

阶段六完成。代码提交 `e1fa91cbce5997f306479cdcb5344d1587c57369`，文档门禁修正提交 `dc705fec087c0b4d41e3a5a85baa38d9811269d8`。准确 SHA `dc705fec` 的 GitHub Actions run `39265415539` 为 17/18 job success；`data-contract` 在既有 40 分钟上限被取消，无测试失败结论。同一 SHA 的独立 Compose 环境执行 CI 同一脚本，133/133 通过且契约摘要检查通过。实现沿用项目已有 ECharts、图表构建器、冻结指标 API、模块 API、深链和来源数据表，没有增加依赖或生成业务数值。

## 实现范围

- CFO 总览优先展示营业收入、营业利润、毛利率和经营现金流四项核心 KPI；营业收入、利润、毛利率及现金流的其他可用指标继续保留为补充 KPI。
- 大额人民币 KPI 按亿元展示并保留两位小数；原始金额仍可从穿透和趋势明细查看。订单量仍按整数显示。
- 营业收入与营业利润趋势各用自己的 Y 轴，避免量级差异把利润线压到零轴；完整趋势明细涵盖 API 返回的每项指标及其期间原值，缺失期间显示为空缺，不补零。
- 总览画布新增/组织现金流变动桥、通过一致性校验的杜邦因子、披露费用排序图、数据期间和来源入口；不同模块披露期间独立标识，不暗示继承总览筛选。
- 费用项目依照真实披露金额呈横向排名；没有多期明细时不伪造按年堆叠趋势。
- 盈利与主题模块页统一采用暖纸白画布、墨蓝层级、克制金色重点；盈利来源事实列表使用稳定唯一键，消除重复 key 告警。
- README 和截图索引纳入当前页面真实截图，并继续明确区分概念板示意数字与合成发行包数据。

## 验证

| 项目 | 结果 |
| --- | --- |
| `pnpm --filter @flow/web test -- --reporter=dot` | 37 个测试文件、196 项通过 |
| `pnpm --filter @flow/web typecheck` | 通过；生产构建亦执行 TypeScript 检查并通过 |
| `pnpm --filter @flow/web build` | Next.js 16.3.3 生产构建通过 |
| `pnpm --filter @flow/web lint` | 0 errors；3 条现有 warning（action-panel 两条、TanStack Table 编译提示一条），本轮新增测试 warning 已清除 |
| `all CFO cockpit views render real charts without narrow-screen overflow` | Playwright 1/1 通过；8 个 CFO 页面与 `/data`，1440×1000 和 390×844 共 18 个页面/视口组合均有真实绘制图表且无页面横向溢出 |
| GitHub Actions run `39265415539`（SHA `dc705fec087c0b4d41e3a5a85baa38d9811269d8`） | 17/18 success；唯一取消为 `data-contract` 达到既有 40 分钟限制，无测试失败报告 |
| `GITHUB_ACTIONS=true bash scripts/test_data_contract.sh`（同 SHA） | 独立 Compose 项目 `flow-contract-dc705-20261019`，133/133 通过，1066.42 秒；摘要 `operating=3072 financial=432 budget=120 ar=1920` 通过 |
| 总览 KPI 与趋势 | 四项 KPI 与完整趋势明细逐项对照 API；页面只有来源支持的期间/原值 |
| 截图浏览器日志 | `pageerror` 0，console warning/error 0 |
| 文档门禁 | 本记录写入后运行 `python3 scripts/check_docs.py --phase m1`；结果随最终提交记录更新 |

## 隔离数据与截图来源

- 独立 Compose 项目：`flow-stage6-cockpit-20261019`，使用专属 PostgreSQL/Redis/MinIO 端口 `25434/26381/29004–29005` 和项目卷；没有连接常驻 `flow` 或 `flow_test`。
- 大麦发行包 manifest SHA-256：`6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed`。
- 批次：`01a15463-cbbc-71dc-8f09-4b4cfdd586d8`。数据明确为大麦物流 synthetic 演示数据，不是真实企业或公开披露数据。
- 图片目录：[cockpit-visual 截图](../../assets/screenshots/cockpit-visual/)。桌面原始视口 1440×900，手机原始视口 390×844；按实际页面全高保存。截图不替换或绘制财务数值。

## 保留的限制

- 本记录证明总览与八个既有主题页面的数据图表、窄屏和局部视觉一致性，不代表公开财报 C 级能力，也不替代真实企业验证。
- 远端 `data-contract` job 仍受 40 分钟上限限制；本阶段依既定替代验收条件以同 SHA 隔离 Compose 133/133 通过结案，不把远端取消描述成成功。
- 项目原有 CI `data-contract` 40 分钟上限及阶段 5 结案限制仍按[门禁验收记录](2026-10-19--ci-concurrency-and-data-contract-isolated-acceptance-v1.md)执行，本阶段没有变更其 timeout 或测试覆盖。
