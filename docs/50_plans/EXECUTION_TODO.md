# 执行待办清单（唯一活跃 TODO）

- doc_id: FLOW-PLAN-EXECUTION-TODO
- 更新：2026-09-24；维护规则：每完成一项打勾并注明提交哈希；新增任务追加到对应分区；本文件由各会话共同维护（写入前先 pull）。
- 依据：D052–D054 战略、[统一计划](2026-09-07-unified-next-plan.md)、[O 计划](2026-09-09-operations-track-plan.md)、[oracle-register](../validation/financial_reports/oracle-register.md)。

## 一、oracle 独立录入线（解锁 U4 首跑）

- [x] zto_2026q1：四 key items + 25 行补充明细录入（`4acc1c3`；用户授权 AI 转录，登记 §1a）
- [ ] tencent_fy2025：key items 录入（282 页年报；收入/净利/Adjusted/经营现金流/主要报表行，定位报表页后转录）
- [ ] sf_2026h1：key items 录入（213 页半年报）
- [ ] 三样本齐后：manifest key_items 升级精确值 + 登记哈希 → **U4 首跑解锁**

## 二、大麦物流实施线（damai-logistics-demo-v1，规格 v1.1）

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
- [ ] U5/U10：按 D053 重新裁决范围

## 四、O 系列经营轨

- [x] O1–O4 全部 done（四样本泛化：顺丰/腾讯/菜鸟/阿里）
- [ ] 阿里 9988 分部披露接入（revenue_structure 增强的数据前提；六份 PDF 已归档）
- [ ] zto 样本抽取（数据未获得，如实标注）

## 五、待用户决策/输入

- [ ] `codex/frontend-consistency-remediation` 分支 UI 路线选型（ui 组件库 vs css 路线；在途修改已保全于分支 `2b53bbe`）
- [ ] U9 内部数据授权（外部依赖）
- [ ] U10 V1.1 证据 go/hold/drop（依赖 U4+U8+U9）

## 六、已完成里程碑（参考，勿重做）

U1–U7 全部 ✅ · U2 全关 ✅ · U5 ✅ · O1–O4 ✅ · 战略沉淀 D052–D054 ✅ · 竞品调研 C01–C20 ✅ · 知识地图 ✅ · 分支清理 ✅（8 删/1 保留）· CI 基线修复 ✅
