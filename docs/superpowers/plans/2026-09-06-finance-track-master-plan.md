# 财务轨完成状态总计划（Master Plan）

- 制定日期：2026-09-06
- 制定依据：D040–D046、用户 2026-09-06 指示（「草案评审不做，按知识库默认推荐方案 + 行业标准定义，继续推进财务轨主线；一次规划到完成状态；计划表可转移、随完成进度沉淀更新」）
- 状态：**执行中**（本文件是财务轨唯一的总计划表，随每一步完成滚动更新；任何 Agent 接手以本文件为起点）
- 基线提交：`6c38f62`（制定时 HEAD）；本文档提交后以实际 git log 为准

---

## 0. 接手 Agent 使用说明（转移协议）

1. **阅读顺序**：仓库根 `AGENTS.md` → `docs/knowledge-base/00_start_here/PROJECT_STATE.md` → 本文件 → `DECISION_LOG.md` 的 D040–D047 → `docs/superpowers/specs/2026-09-05-flow-metric-dictionary-design.md`（指标库正式规格）。
2. **执行纪律**（每个任务都适用）：
   - TDD（先测后码）；改完跑门禁；`make contracts-check` 守护契约；
   - 不修改已冻结契约（`flow.excel.v1`、`flow.metrics.logistics.v1` 迁移完成前）、不绕过 D016/D028/D031/D033/D037 确定性与不可变边界；
   - 不删除/不改写原始档案（`docs/knowledge-base` 的 raw/original/p5_samples）；
   - 红线操作（删文件、密钥、schema 变更之外的破坏性操作、强推）先问用户。
3. **完成一个任务的固定动作**：
   ① 本文件任务表状态改 `done` 并写证据链接 → ② 更新 `PROJECT_STATE.md` 对应阶段 → ③ 动过 `docs/knowledge-base` 则重生成 `99_manifest` → ④ 范围明确的 commit → ⑤ push → ⑥ **CI 全绿后**才算完成；CI 红先修再继续。
4. **额度不足交接**：在「第 6 节 当前执行点」写清——正在做哪个任务、已完成到哪一步、下一步第一条命令是什么。接手 Agent 从那里继续，不需要任何对话上下文。
5. **默认推荐策略（D047，用户已确认）**：不做逐项人工评审。以微信知识库（数据熊等）方案为默认推荐结构，Obsidian 菜鸟材料为事实依据，行业标准定义（CAS、国资委、CPA、CFA，见调研 07–11 号资料）为口径校准；口径分歧时「行业标准/准则原文为默认口径，备选口径并存记录」。

## 1. 财务轨「完成状态」定义（DoD）

财务轨视为完成，当且仅当以下全部成立：

1. 指标字典与会计基础数据定稿（v1.0），版本化于 `config/`，含门禁；
2. 经营轨数据定义按同一策略同步定稿 v1.0（不阻塞财务轨，但随本计划一并收口）；
3. 指标库、会计科目、分录模板、报表项目映射全部落库（P3），系统页面读数据库；
4. `flow.metrics.logistics.v1` 迁移为库内行业指标集，引擎从库读取，**全部既有门禁保持绿**（P4）;
5. P5 验证实验完成：顺丰（已完）、腾讯（已完）、京东物流（待做）三公司四表一注重建 + 反向生成完整分析报告并与披露逐项比对，差异三级分类留痕；
6. 四表一注作为报告类型接入统一发布管线（冻结快照 → XLSX/HTML/PDF，黄金值门禁）；
7. Pilot Phase 2 收尾：备份恢复演练、部署拓扑与 HTTPS、结构化日志、验收证据（D038 Task D–G），以及**脱敏真实数据试点**（T6.6）；
8. 试点/验证证据汇总为 V1.1 决策包；全程 CI 保持绿。

## 2. 当前基线快照（2026-09-06，HEAD `6c38f62`）

- 已完成：Phase 1–10 全部功能切片；Pilot Phase 1 用户闭环（基线 `v0.2-pilot-baseline`）；指标库 v0 数据集（40 通用 + 15 物流 + 164 科目 + 11 准则 + 17 分录模板）并已入系统（`/metric-library` + `GET /api/v1/metric-library`）；报表分析页 `/statements`（迁移 0011 + typed API）；P5 抽取管道（顺丰 2026Q1 ✅、腾讯 2026Q2 ✅、抽取层已接 `StatementLineItem` 模型与 AST 指标引擎）；S3 代理根因修复（boto3 系统代理问题，真实 MinIO 链路已验证）；双轨产品结构（D045，`/operations` 演示页）。
- 未完成：主 CI 红（见 WS-0）；指标字典/会计基础 v1.0 定稿；经营轨定稿；P3 数据库化；P4 迁移；京东物流抽取；四表一注进发布管线；D038 Task D–G；V1.1 决策包。

## 3. 工作流总览

| 工作流 | 内容 | 依赖 | 状态 |
|---|---|---|---|
| WS-0 | 基线修复：恢复主 CI 绿 | 无 | pending |
| WS-1 | 定稿与默认推荐策略（D047）落地 | WS-0 | pending（T1.1 done） |
| WS-2 | P3：指标库/报表项目数据库化 | WS-1 | pending |
| WS-3 | P4：物流指标集迁移 | WS-2 | pending |
| WS-4 | P5：验证实验收口（京东物流 + 反向生成报告） | WS-2（可与 WS-3 并行） | pending |
| WS-5 | 四表一注接入统一发布 | WS-3 | pending |
| WS-6 | Pilot Phase 2 收尾（D038 Task D–G） | 无（可随时插入） | pending |
| WS-7 | V1.1 决策包 | WS-3/4/6 | pending |

## 4. 任务明细

### WS-0 基线修复

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T0.1 | 修复 `7e3640e` 导航三组重组引入的 axe serious 违规 | CI 全部 16 job 绿 | **done**（`34c3bd8`：根因为 `.workflow-rail__group-label` 灰蓝 `#6d7f99` 对深底 3.9:1，调亮为 `#8fa2bd` 达 6.13:1；本地 dashboard 7/7、investigation 4/4 通过） |

### WS-1 定稿与默认推荐策略（D047）

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T1.1 | 记录 D047 默认推荐策略进决策日志 | DECISION_LOG D047 条目 | done（本计划同轮提交） |
| T1.2 | 指标字典 v0 → v1.0 定稿（15 项口径裁决：default_caliber/default_basis/alternative_calibers） | 脚本 `scripts/finalize_metric_dictionary.py` 自检 + API 契约测试 | **done**（`config/metrics/metric_dictionary_v1.yaml`，status=effective） |
| T1.3 | 会计基础补全 | 结构自检（科目唯一/准则唯一/模板唯一/引用闭合）+ API 契约测试 | **done**（`accounting_foundation_v1.yaml`：科目 167、准则 48=基本+42 项+汇编+IFRS 对照、分录 32；1802/2703 编号正式化；剩余缺口如实标注） |
| T1.4 | 经营轨数据定义 v0 → **v1.0 定稿**（D047 策略，数据熊方案为默认结构 + 行业标准校准）：`config/metrics/operations_dictionary_v1.yaml`；物流专营指标缺口保留显式标注 | 结构校验通过 + 定义文件落盘（`/operations` 页改读经营轨定义，待经营轨数据管线接通后另行绑定，不在本任务验收内） | pending |
| T1.5 | 系统指标库页面切换 v1.0 数据源 | API/页面/契约测试全绿 + 浏览器验收 | **done**（路由切 v1 路径、schema 增 default_caliber 等字段、测试锁定 v1；本地栈验证 `/metric-library` 经代理返回 v1） |

### WS-2 P3：指标库/报表项目数据库化

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T2.1 | 迁移 0012 五张表 | `check_migrations` 往返通过 | **done**（`0012_metric_library_objects`，往返验证通过） |
| T2.2 | 导入器（幂等 upsert） | 契约测试 | **done**（`flow_api/metric_library_store/importer.py` + `POST /api/v1/metric-library/import`） |
| T2.3 | 版本化变更流程 | 契约测试 | **done**（retire 端点 + JSONL 审计；导入幂等承担版本演进） |
| T2.4 | 页面数据源切 DB | 契约/组件测试 | **done**（DB 优先 + YAML 兜底，9 项测试绿；页面消费同一 typed API 无需改动） |
| T2.5 | 报表项目 ↔ 科目映射 | 溯源闭合测试 | **done**（`REPORT_ITEM_SUBJECTS` 显式映射 + 编码存在性闭合校验） |
| T2.6 | 发布后编排入口 | 3 项契约测试（幂等/404/409） | **done**（`POST /api/v1/orchestration/batches/{id}/build`：快照序列 + 分析运行串联） |

### WS-3 P4：物流指标集迁移

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T3.1 | 物流指标集库内化 | 已知答案一致 | **done**（迁移 0013 `metric_catalog_document` + `metrics_store` 存取层；6 项一致性门禁含快照身份链实证） |
| T3.2 | 生产加载路径切库内优先 | 门禁绿 | **done**（orchestration 与 dashboard fixture 切 `resolve_metric_catalog`；metrics-known-answers/analysis-invariants/dashboard 三道门禁本地 PASS，哈希与基线一致；publishing/intake/investigation 由 CI 同批验证） |
| T3.3 | 兼容读取期与记录 | D048 + 阶段记录 | **done**（D048：YAML 兜底保留至 V1.1 评审后议退役） |

### WS-4 P5：验证实验收口

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T4.1 | 京东物流 FY2025 年报抽取 | 勾稽校验 | **done**（`p5_extract_jdl.py`：IFRS 勾稽 24/24；另补腾讯 `p5_extract_tencent.py` 20 行 + 调节链闭合） |
| T4.2 | 三公司统一视图接入 `/statements` | 页面可见 | **done**（三司落库：163+20+118 行项目，列表/详情/图形页面切换正常） |
| T4.3 | 反向生成报告并逐项比对 | 证据归档 | **部分完成**（事实层/指标计算/视图/锚点比对一致，见 [P5-validation-summary](../../implementation/p5/P5-validation-summary.md)；全行项目 diff 表随 WS-5 报告管线收口） |
| T4.4 | P5 证据文档 | 文档落盘 | **done**（`docs/implementation/p5/P5-validation-summary.md`） |

### WS-5 四表一注接入统一发布

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T5.1 | Report Snapshot 扩展「四表一注」报告类型（沿用冻结 JSONB + 不可变触发器模式） | 迁移 + 契约测试 | pending |
| T5.2 | XLSX / HTML / PDF 渲染器 + 黄金值门禁（跨格式关键值一致） | `make test-publishing-golden` 扩展 | pending |
| T5.3 | 报告中心 UI：四表一注与现有月报并列可选 | 组件测试 + e2e | pending |
| T5.4 | PDF 打印器接入（固定 Chromium 打印进程注入发布管线），现有月报 PDF 从「无打印器必 failed」转为可生成；README 边界说明同步更新 | PDF 产物黄金值门禁含 PDF | pending |

### WS-6 Pilot Phase 2 收尾（D038 Task D–G）

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T6.1 | 密钥出仓复核（Task C 已有基础的核查与补漏） | 无密钥入代码/日志 | pending |
| T6.2 | 备份与恢复演练（Task D：PostgreSQL dump/restore + 对象存储恢复） | 演练记录落盘 | pending |
| T6.3 | 部署拓扑与 HTTPS（Task E：反向代理、证书、网络边界） | 部署手册 + 实测 | pending |
| T6.4 | 结构化日志与关联 ID（Task F） | 日志含 request/batch 关联 ID | pending |
| T6.5 | 验收门禁与证据（Task G：运维验收文档） | 文档 + 门禁脚本 | pending |
| T6.6 | 脱敏真实数据试点（D038 关键链路：安全部署之后、V1.1 之前；脱敏规则 + 试点数据导入 + 可复核业务价值证据）——缺此任务则 WS-7 无试点证据可用 | 试点证据文档落盘 | pending |

### WS-7 V1.1 决策包

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T7.1 | 指标阈值与预警规则明细（依据试点/验证暴露的真实口径，D038 尾项） | 明细表落盘 | pending |
| T7.2 | 证据汇总 → V1.1 决策材料（P5 三公司验证 + 试点结果 + 双轨 demo 反馈） | 决策文档 | pending |
| T7.3 | FLOW 正式品牌释义（未决项，可选） | 用户确认 | pending |

## 5. 推荐执行顺序

```
WS-0 → WS-1（T1.2/T1.3 可并行 T1.4）→ WS-2 → WS-3 ─┬→ WS-5 → WS-7
                └──────────────────────────────────┴→ WS-4（可与 WS-3 并行）
WS-6 独立，可在任意 WS 之间插入（建议在 WS-3 后、WS-7 前）
```

## 6. 当前执行点（交接断点写在这里）

- 状态：WS-0–WS-4（主体）全部 done 且 CI 全绿（最新 `0c263d6`，run 34020791625 全 16 job 通过，含 smoke 容器栈验证）；期间修复编排路由在容器内路径越界导致 smoke 红的问题（DASHBOARD_MONTHS 抽 constants 模块 + 惰性仓库根解析）。
- 下一步：进入 WS-5 四表一注接入统一发布——先做 T5.1（Report Snapshot 扩展「四表一注」报告类型：沿用冻结 JSONB + 不可变触发器模式，迁移 0014），再 T5.2 渲染器（XLSX/HTML/PDF + 黄金值）与 T5.4（固定 Chromium 打印器注入发布管线）；完成后回头收口 T4.3 的全行项目 diff 表。

## 7. 变更日志

| 日期 | 变更 | 操作者 |
|---|---|---|
| 2026-09-06 | 初版：合并 D040–D046 全部待办，形成 WS-0–WS-7 总计划；同轮记录 D047 | ZCode |
| 2026-09-06 | WS-0 done（`34c3bd8`）：nav 分组标签对比度 3.9→6.13:1；进入 WS-1 | ZCode |
| 2026-09-06 | WS-1 done：三个 v1 定稿（指标字典 15 裁决 / 会计基础 167+48+32 / 经营轨 6 域 43 指标）+ 页面切 v1 + 契约重生成；进入 WS-2 | ZCode |
| 2026-09-06 | WS-2 done：迁移 0012 五表、幂等导入器 + import/retire 端点 + 审计、DB 优先读取、报表项目↔科目映射闭合、发布后编排入口（T2.6）；mypy/ruff/契约/9 项测试绿 | ZCode |
| 2026-09-06 | WS-3 done（D048）：迁移 0013 目录文档库内化、resolve 库内优先、6 项一致性门禁（快照身份链实证 = 基线哈希）、metrics/analysis/dashboard 三道门禁 PASS | ZCode |
| 2026-09-06 | WS-4 主体 done：JDL 抽取 24/24 + 腾讯抽取（新脚本）+ 三司落库 `/statements` + P5 证据汇总；T4.3 完整 diff 随 WS-5 收口 | ZCode |
| 2026-09-06 | 修复 smoke：编排路由模块级 `parents[6]` 在容器内越界 → DASHBOARD_MONTHS 抽 `dashboard/constants.py`、仓库根改惰性解析（`0c263d6`，CI 恢复全绿） | ZCode |
| 2026-09-06 | Review 修正（Kimi）：补齐三个范围缺口——T2.6 发布后编排入口（新批次一键出指标/分析）、T5.4 PDF 打印器接入、T6.6 脱敏真实数据试点（D038 链路缺环）；T1.4 验收改为定义落盘（/operations 绑定待经营轨数据管线）；决策日志「未来与未决事项」过期引用改为 D045 | Kimi |
