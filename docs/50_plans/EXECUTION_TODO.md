---
doc_id: FLOW-PLAN-EXECUTION-TODO
title: 执行待办清单（唯一活跃 TODO）
doc_type: navigation
status: current
version: 1.0
created_at: 2026-09-24
updated_at: 2026-09-24
owner: FLOW
applies_to: repository
---

# 执行待办清单（唯一活跃 TODO）

- doc_id: FLOW-PLAN-EXECUTION-TODO
- 更新：2026-09-24（晚间决策问答轮）；维护规则：每完成一项打勾并注明提交哈希；新增任务追加到对应分区；本文件由各会话共同维护（写入前先 pull）。
- 依据：D052–D054 战略、[统一计划](2026-09-07-unified-next-plan.md)、[O 计划](2026-09-09-operations-track-plan.md)、[oracle-register](../validation/financial_reports/oracle-register.md)。

## 一、oracle 独立录入线（解锁 U4 首跑）

- [x] zto_2026q1：四 key items + 25 行补充明细录入（`4acc1c3`；用户授权 AI 转录，登记 §1a）
- [ ] tencent_fy2025：key items 录入（282 页年报；**AI 转录已获授权 2026-09-24**，待独立会话执行）
- [ ] sf_2026h1：key items 录入（213 页半年报；**AI 转录已获授权 2026-09-24**，待独立会话执行）
- [ ] 三样本齐后：manifest key_items 升级精确值 + 登记哈希 → **U4 首跑解锁**

## 二、大麦物流实施线（damai-logistics-demo-v1，规格 v1.1）——用户拍板双线推进（2026-09-24）：本线与 oracle 录入线并行，本分支为活跃工作区

- [x] Task 1 公司画像冻结（`dd875f3`，7 测试）
- [x] Task 2 canonical 数据集生成器 + 验证器（`19625a1`，9 测试；forecast sidecar static-only）
- [x] Task 3 闭合财务报告 FY2025/FY2026（`946aa31`，六大恒等锚；51e92b2 重放）
- [x] Task 4 slice-1 装载器财报子链（`b5b3354`：enterprise upsert + 两报告导入/归一化/发布，2 测试）
- [ ] Task 4 slice-2：指标快照 ×12 + AnalysisRun + Finding/Evidence/Conclusion 状态机编排 + 事务回滚注入测试
- [ ] Task 5：客观报告冻结（接 U5 资格合同）+ 经营概览快照
- [ ] Task 6：damai_demo_metric_coverage_v1 数据集 + API dataset 参数 + 前端切换
- [ ] Task 7：make damai-demo-build/seed/verify/up 四入口
- [ ] Task 8：八页面 E2E 验收（含真实 /data 上传旅程，不得以 seed 后非空代替）
- [ ] Task 9：全量回归 + 文档刷新 + 交付关闭（严格最终 SHA CI 语义）

## 三、U 系列财务轨（主线性任务）

- [x] U1–U7 全部 done
- [ ] U4 独立全行验证：依赖一（oracle 三样本）
- [ ] U8 收口：真实存储完整旅程、HTTPS 部署拓扑、统一部署验收（D052 后最高优先；U8-C 结构化日志已交付）
- [ ] U5/U10：按 D053 重新裁决范围（U10 用户倾向 go，2026-09-24；依赖 U4+U8+U9 到齐后启动）

## 四、O 系列经营轨

- [x] O1–O4 全部 done（四样本泛化：顺丰/腾讯/菜鸟/阿里）
- [ ] 阿里 9988 分部披露接入（revenue_structure 增强的数据前提；六份 PDF 已归档；**用户批准抽取 2026-09-24**）
- [ ] zto 样本抽取（数据未获得；**用户批准寻找公开渠道获取 2026-09-24**）

## 五、待用户决策/输入

- [x] `codex/frontend-consistency-remediation` 分支：**保留分支结案**（2026-09-24 问答轮；不入 main，从待决清单移除）
- [x] U9 内部数据授权：**按 roadmap 顺序**，C 级出口完成后再启动（2026-09-24）
- [x] U10 V1.1 证据决策：用户倾向 **go**（2026-09-24；依赖 U4+U8+U9 到齐后按预置决策包启动）

## 五-b、决策日志（2026-09-24 问答轮，AskUserQuestion 两轮共 8 项）

1. 主线优先：**双线推进**——大麦线（本分支）与 oracle 录入线（独立会话）并行。
2. oracle AI 转录授权：**腾讯 fy2025 + 顺丰 2026h1 两份一次性授权**（与 zto 同模式，须独立会话执行）。
3. M2 原子激活（962b651，CURRENT_RELEASE 切换）：用户**追认有效**；后续知识工作（v2 刷新/增量扫描/roadmap v1.7）引用链无需变动。
4. 压力测试 10 条抽取错误候选：**按 AI 判断直接修正**（用户明示选择；执行时逐条在订正层登记原值/新值/依据，保留审计痕迹）。
   **已关闭（2026-09-25）**：10 条全部为误报（8 条符号印刷差异 + 2 条图像页），经订正层登记（validation/financial_reports/corrections.md）；顺带修复 2023fy 上期列 23 项 + 2019fy NCI 上期误抓；L1 覆盖率 1794/1794=100%、双零维持。
5. 前端遗留分支：**保留结案**（不入 main，不删）。
6. O 系列数据扩张：**批准阿里 9988 抽取 + 授权寻找 zto 公开数据**。
7. U9 授权时机：**按顺序**（C 级出口完成后启动）。
8. U10：**倾向 go**（未启动；U4 首跑后按预置决策包走）。

## 六、已完成里程碑（参考，勿重做）

U1–U7 全部 ✅ · U2 全关 ✅ · U5 ✅ · O1–O4 ✅ · 战略沉淀 D052–D054 ✅ · 竞品调研 C01–C20 ✅ · 知识地图 ✅ · 分支清理 ✅（8 删/1 保留）· CI 基线修复 ✅
