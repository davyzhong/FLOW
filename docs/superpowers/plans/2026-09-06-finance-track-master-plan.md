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
7. Pilot Phase 2 收尾：备份恢复演练、部署拓扑与 HTTPS、结构化日志、验收证据（D038 Task D–G）；
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
| T0.1 | 修复 `7e3640e` 导航三组重组引入的 axe serious 违规（`dashboard` 与 `investigation-e2e` 两 job 红；违规为对比度/页面结构类，涉及 `workflow-nav.tsx`、`operations.css`），修后本地 `npx playwright test apps/web/e2e/dashboard*.spec.ts apps/web/e2e/investigation.spec.ts` 复现路径验证 | CI 全部 16 job 绿 | pending |

### WS-1 定稿与默认推荐策略（D047）

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T1.1 | 记录 D047 默认推荐策略进决策日志 | DECISION_LOG D047 条目 | done（本计划同轮提交） |
| T1.2 | 指标字典 v0 → **v1.0 定稿**：口径分歧项按 D047 规则敲定默认口径（ROE 平均口径、DSO 360 天、存货周转营业成本分子等，以准则/CPA/国资委为据），备选口径并存；补齐 benchmark 字段（国资委标准值/联合资信基线）；产出 `config/metrics/metric_dictionary_v1.yaml`（新版本文件，不改 v0） | YAML schema 校验脚本 + `make contracts-check` + `/metric-library` 显示 v1.0 | pending |
| T1.3 | 会计基础补全：科目 164 → 171 全量（缺口 8 个 2024 新增，按调研 10 号来源策略交叉拼合并标注置信度与出处）；准则登记册 11 → 42 项全量；分录模板 17 → 30+（数据熊分录大全 + 菜鸟场景，参照调研 07 号） | 会计基础 v1.0 配置 + 结构校验 | pending |
| T1.4 | 经营轨数据定义 v0 → **v1.0 定稿**（D047 策略，数据熊方案为默认结构 + 行业标准校准）：`config/metrics/operations_dictionary_v1.yaml`；物流专营指标缺口保留显式标注 | 结构校验 + `/operations` 页与定义一致 | pending |
| T1.5 | 系统指标库页面与评审台数据源切换 v1.0 | `/metric-library` 渲染 v1.0 内容 | pending |

### WS-2 P3：指标库/报表项目数据库化

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T2.1 | 迁移 0012：`metric_dictionary_entry`、`accounting_subject`、`accounting_standard`、`entry_template`、`statement_line_mapping` 表（uuid7 主键、版本字段、Numeric(24,4)） | `check_migrations` 往返通过 | pending |
| T2.2 | 导入器：v1.0 配置 → 数据库（幂等，版本化）；度量/科目/分录/映射四类 | 契约测试 | pending |
| T2.3 | 版本化变更流程 API：草案 → 生效 → 废止 + 审计记录（沿用 ReviewEvent 风格） | typed 契约测试 | pending |
| T2.4 | `/metric-library` 页面数据源从 YAML 切换为 DB（typed API，经生成契约） | 组件测试 + e2e | pending |
| T2.5 | 报表项目 ↔ 科目映射接通：`/statements` 行项目可溯源到科目与指标 | 映射 API 契约测试 | pending |

### WS-3 P4：物流指标集迁移

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T3.1 | `flow.metrics.logistics.v1` 的 15 指标 + 14 依赖边迁移为库内「物流行业指标集 v1」（来源：库内定义，`migrates_from` 溯源） | 已知答案值逐项比对一致 | pending |
| T3.2 | 引擎、驾驶舱投影、报告管线改从库内指标集读取；快照身份链与 `definition_set_hash` 演进规则不变 | 全部门禁绿：`make acceptance`（含 metrics-known-answers、analysis-invariants、publishing-golden、intake、investigation、user-closure） | pending |
| T3.3 | 旧代码内目录退役（保留一个版本的兼容读取期），文档与决策日志记录迁移完成 | PROJECT_STATE 阶段记录 | pending |

### WS-4 P5：验证实验收口

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T4.1 | 京东物流 FY2025 年报抽取（扩展 `p5_extract_statements.py` alias map；披露易 PDF） | 勾稽校验通过 + 差异留痕 | pending |
| T4.2 | 三公司统一报告视图重建（顺丰 ✅、腾讯 ✅、京东物流）并接入 `/statements`（经导入器落库） | 三份报表在系统页面可见 | pending |
| T4.3 | 反向生成完整分析报告（四表一注 + 指标 + 分析叙事）并与披露逐项比对；差异分级：口径差异 / 解析误差 / 披露缺失，全部留痕归档 | 比对表归档为验证证据 | pending |
| T4.4 | P5 验证证据文档 + PROJECT_STATE 阶段记录 | 文档落盘 | pending |

### WS-5 四表一注接入统一发布

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T5.1 | Report Snapshot 扩展「四表一注」报告类型（沿用冻结 JSONB + 不可变触发器模式） | 迁移 + 契约测试 | pending |
| T5.2 | XLSX / HTML / PDF 渲染器 + 黄金值门禁（跨格式关键值一致） | `make test-publishing-golden` 扩展 | pending |
| T5.3 | 报告中心 UI：四表一注与现有月报并列可选 | 组件测试 + e2e | pending |

### WS-6 Pilot Phase 2 收尾（D038 Task D–G）

| ID | 任务 | 验收 | 状态 |
|---|---|---|---|
| T6.1 | 密钥出仓复核（Task C 已有基础的核查与补漏） | 无密钥入代码/日志 | pending |
| T6.2 | 备份与恢复演练（Task D：PostgreSQL dump/restore + 对象存储恢复） | 演练记录落盘 | pending |
| T6.3 | 部署拓扑与 HTTPS（Task E：反向代理、证书、网络边界） | 部署手册 + 实测 | pending |
| T6.4 | 结构化日志与关联 ID（Task F） | 日志含 request/batch 关联 ID | pending |
| T6.5 | 验收门禁与证据（Task G：运维验收文档） | 文档 + 门禁脚本 | pending |

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

- 状态：**计划已批准待开工**；未执行任何任务。
- 下一步第一条命令：`make test-dashboard`（复现 WS-0 的 axe 红CI）→ 修 `workflow-nav.tsx` / `operations.css` 相关样式 → 本地 `npx playwright test apps/web/e2e/dashboard*.spec.ts` 验证 → push 看 CI。

## 7. 变更日志

| 日期 | 变更 | 操作者 |
|---|---|---|
| 2026-09-06 | 初版：合并 D040–D046 全部待办，形成 WS-0–WS-7 总计划；同轮记录 D047 | ZCode |
