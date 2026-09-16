---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目尽调、优化与单 Agent 执行总交接
doc_type: navigation
status: current
version: 3.2
created_at: 2026-09-12
updated_at: 2026-09-15
owner: FLOW
applies_to: repository
---

# FLOW 项目尽调、优化与单 Agent 执行总交接｜2026-09-15

> 本页是下一位单一 Agent 的工作入口，整合了多 Agent 执行审计、R1 修复复核、竞品与方法论研究、工程收口计划和后续产品优化建议。它负责说明“现在在哪里、还要查什么、先改什么、怎样证明完成”；项目状态仍以 [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md) 为唯一事实源，任务顺序仍以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为唯一执行入口。

## 0. 执行摘要

### 0.1 当前可信结论

- **当前基线：`main@80b21e6`**（m6 门禁生效 + 实施证据登记）；本会话交付批次终点 `2e6cc1e`（C 级出口执行批次），此后有并行会话的 docs 提交（README 升级/链接修复，至 `1325cf7`），均在 m6 门禁守护下。
- **S01 已正式关闭**（R2/R3/R4 + Task 6 关闭，登记于协调台账 §7）；U8 关闭不变。
- **阶段 3 基础（T09–T12）已交付**（台账 §8）：L0 基准 1454/1454、L1 页级答案集 1775/1795（98.9%）双零验证、数据点级溯源 95.5% 带页锚、重述 supersedes 链 + diff、只读 MCP 三工具、确定性差异起草、10× 性能基线（P95 明细 4.4/检索 1.0/聚合 1.7ms）、问数 v1 + 94 问评测 100% 命中。
- **C 级出口执行批次已交付**（台账 §9）：压力测试抓获 10 条抽取错误候选；holdout 预注册签封；AI 交叉评执行包；性能门禁入 CI（P95≤50ms）；m6 文档门禁入 CI（G6 关闭，用户批准 `fbe8296`）。
- 多 Agent 并行已终止，采用**单一 Agent、逐 Gate、串行执行**；历史 Sol/Kimi/GLM 名称只表示审计来源，不表示新的并行派工。
- 产品战略方向无跑偏：核心是“经分专员使用的财务经营分析工作台”，系统自主完成数据/证据/分析/草稿，经分专员统一终审发布；公开财报是独立先行模块。
- **出口裁决参数已由用户苏格拉底问答确认**（协议 §3.7）：两层 holdout、回归层=菜鸟压力测试、全量 100% 零容忍（分母=已定位值，未定位人工补齐）、纯 AI 交叉评（无人工兜底，独立性声明如实打折）、新批次预注册随机抽签。
- **下一里程碑 = C 级出口 Go/No-Go 裁决**；前置仅剩三件轻量人工项 + A4 外部材料（见 §8）。

### 0.2 当前最重要的偏差与缺口

| 类型 | 当前判断 | 处理方式 |
|---|---|---|
| 10 条抽取错误候选 | BABA NCI 行（-9083/-7652 等 8 条）+ JDL 现金流 2 行的值在源 PDF 文本层不存在——**压力测试实锤，不是定位技术问题** | 人工翻页查源（压力测试报告 §2 清单）→ 修抽取 YAML 新版本 → 重跑基准 |
| C 级出口 PASS | 证据链已就绪，缺独立盲评与 holdout 执行 | 用户执行 AI 交叉评（包已备）+ 到料后抽签 |
| 数据扩张 | 10 家公司真实财报 PDF 未到料 | A4 外部材料；到料即走既有管线 |
| 合规尽调 G4 | 未启动 | A5；阻塞 T13 与 MCP/LLM 开放 |
| 运行产物/owner 命名 | 已清理（var/ 出库、owner 职责域化） | 已闭环 |

## 1. 权威关系与阅读顺序

下一位 Agent 开始工作时按以下顺序读取，禁止从历史聊天或旧三 Agent 计划直接领任务：

1. [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md)：唯一 current state；
2. [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md)：唯一可领取路线图；
3. [S01 工作包](docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）与 [C 级出口工作包](docs/50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（当前 Gate，含 §3.7 出口裁决参数）；
4. [战略重构设计 V1.1](docs/superpowers/specs/2026-09-13-flow-strategic-reset-design.md)、[PRODUCT_SCOPE](docs/20_product/PRODUCT_SCOPE.md)、[PRODUCT_PRINCIPLES](docs/20_product/PRODUCT_PRINCIPLES.md)：产品目标、固定原则和冲突裁决；
5. [协调台账](docs/70_operations/2026-09-14-coordination-ledger-glm.md) §6/§7/§8/§9：R0/R1、R2/R3/R4、T09–T12、C 级出口执行批次的全部完成证据；
6. [整合尽调总汇](docs/80_reviews/2026-09-15-integrated-due-diligence.md)、[整合优化方案](docs/80_reviews/2026-09-15-integrated-optimization-program.md)：审计结论与候选优化项；
7. [竞品优化清单](docs/competitive/optimization-checklist.md)与[知识库 O-01～O-17](docs/knowledge-base/09_competitive/2026-09-14-optimization-backlog.md)：只作候选需求证据。

冲突裁决顺序：用户最新明确指令 → 已接受决策 D052–D054 → approved 规格 → PROJECT_STATE → CURRENT_ROADMAP / 当前工作包 → 本交接 → review / research → 历史计划和聊天记录。

## 2. 本会话（2026-09-15 执行批次）交接明细

### 2.1 已完成（全部推送 main，CI 全绿）

| 批次 | 内容 | main 锚点 |
|---|---|---|
| R2/T02–T04 | 治理写 7 条策略化（proposed_by fail-closed）；四阶段发布 ABI（迁移 0028，Idempotency-Key 必填，intent/outcome 503）；旁路 pipeline 删除；§3.3 身份字段全链 Principal 化（UI/测试不发 actor/reviewer/operator）；卫生包（var/ 出库、owner 职责域化） | `5d085b4`→`a16751e` |
| R3/T06 | module-boundaries-v2：ownership v2（glob_rules + catch-all 全树唯一 owner）、`scripts/check_module_boundaries.py` 全树 AST + import_rules、违规 fixture 证明能红 | `fbfe7d8` |
| R4/T07 | `scripts/r4_full_verification.sh`：隔离 compose + 动态端口 + 真实 CA + dump 四证 → 升级 0028 → SQL==HTTPS 双证明，本地 PASS；minio pin `RELEASE.2025-04-22T22-12-26Z`（:latest 漂移曾致多 job 红） | `2fa5f72` |
| T08 | S01 关闭 + 权威文档同步（PROJECT_STATE v1.7、HANDOFF v3.1、台账 §7） | `6431cf2` |
| T09 | L0 基准 1454/1454；L1 页级答案集 1775/1795（98.9%，strong 980/weak 795）双零验证；裁决参数 §3.7（苏格拉底问答） | `5a9e788`/`ffef522` |
| T10 | 迁移 0029（溯源列 + supersedes_id）；导入器溯源认领 95.5%；`statement_restatement_diff.py`；`mcp_facts_server.py`（token fail-closed）；`draft_restatement_commentary.py` | `c9dcd47`/`dda978b` |
| T11-G2 | `perf_baseline.py` 10× 事务内放大（回滚无污染），P95 明细 4.4/检索 1.0/聚合 1.7ms | `8c479a1` |
| T12 | `ask_facts.py` 确定性问数 v1（拒答零误答）+ `generate_qa_eval.py` 94 问评测 100% 命中 | `ffef522` |
| C 级出口执行 | 菜鸟压力测试（抓获 10 条抽取错误候选）；holdout 预注册签封；AI 交叉评执行包 + 证据束导出；C1 性能门禁入 CI；m6 入 CI（用户批准，G6 关闭） | `44acd16`→`2e6cc1e`/`fbe8296` |

### 2.2 卡住的问题（全部为外部/人工依赖，非技术阻塞）

1. **10 条抽取错误候选人工查源**：BABA 利润表「歸屬於非控制性權益損益」8 条（-9083/-7652 等值在源 PDF 全文本层不存在，p38 实际为 2,534/2,872/4,067/6,529 系）+ JDL「存放受限制現金」「已付利息」2 条。清单在 `docs/60_delivery/2026-09-15-cainiao-stress-test-report.md` §2。需要人翻 PDF 确认原始数字，之后修抽取 YAML（新版本文件）并重跑基准（预期覆盖 ≥99.4%）。
2. **AI 交叉评执行**：包与 prompt 已备（`docs/80_reviews/ai-cross-review/README.md`），证据束导出命令 `--export-review-bundle`（工作产物不进 git）。需要用户开一个非 GLM 会话逐份粘贴执行——实现方（GLM）不得自评。
3. **A4 扩张材料**：10 家公司真实财报 PDF 未到料——不可合成，到料即走既有管线（含 holdout 抽签）。
4. **A5 合规尽调 G4**：未启动；阻塞 T13、MCP 开放（C2 已记录悬置）、T12 LLM 通道。
5. **U4 oracle / rnd_exp 原文 / U9·O5 / U10**：外部材料与授权，同前不变。

### 2.3 下一步计划（下一 Agent 按序领取）

1. 收到 10 条人工查源结果 → 修抽取 YAML → 重跑 `build_answer_set_l1.py` + `accuracy_benchmark.py` 双层 → 更新压力测试报告；
2. 用户执行 AI 交叉评后 → 逐条归因（真错修管线 / 误报留档）写 `results/adjudication.md`；
3. A4 到料 → 抽签（预注册规则）→ 批次 1 扩张（抽取 → L0/L1 → 冻结 → 重述链实战验证）；
4. 三项齐备 → **C 级出口 Go/No-Go 裁决** → 通过后解锁 T13（需 A5）与 T12 LLM 通道；
5. 同步纪律：每步完成即更新路线图/台账/PROJECT_STATE 并同 SHA CI 全绿。

### 2.4 本会话踩过的坑（新增，接续 §7）

- **批量还原“噪音”文件前必须 dry-run 验证排除正则**：R2 曾因排除正则漏配 `.py` 后缀分支，把自己的修改 checkout 回退并随提交污染分支（CI 红在 import 上才暴露）。教训已入记忆 `flow-git-revert-noise-lesson`；
- **管道 tail 吞退出码**：`python3 check_docs | tail` 的退出码是 tail 的——门禁失败被吞、提交先行为发生。门禁命令必须独立执行或用 `set -o pipefail`；
- **m6 文档门禁的红点谱系**：views 漂移（改路线图后必须 `plan_views.py --write`）、生成物无 frontmatter（证据束等工作产物放 `work/` 不进 git）、doc_type×status 词表（delivery 用 `verified` 非 delivered；work-item 无 sealed——签封件用 plan+active+sealed_by 自定义字段）；
- **Quay `minio:latest` 上游漂移**：新版拒绝 bootstrap 凭据致多 job 红——已 pin `RELEASE.2025-04-22T22-12-26Z`，新增第三方镜像一律 pin；
- **裸 Connection 的 entity select 返回列值行而非 ORM 对象**：独立脚本查询必须显式列（`statement_restatement_diff.py` 教训）；
- **psycopg text() 双冒号 cast**：`:param::uuid` 解析失败，必须 `CAST(:param AS uuid)`（二次踩坑，老坑新形态）；
- **§3.3 横切合同**：require_action 对 POST/PUT/PATCH 预读 body 做身份冲突检测——任何 UI/测试发 `actor/reviewer/operator` 字段都会 409；新增写路由一律从 AuthorizationContext 取身份；
- **bash 全角括号内的 `$VAR` 会被解析成长变量名**（`（project=$PROJECT，` → unbound）；脚本内一律 `${PROJECT}`；
- **setup-uv 缓存 Post-run 偶发报错**：重跑 failed jobs 即过，属环境性 flake，不算门禁失败。

## 3. 完整尽调计划（触发条件与频率不变）

| ID | 尽调包 | 触发 |
|---|---|---|
| DD0 | 基线冻结与证据盘点 | 每次会话开始（轻量版） |
| DD1–DD9 | 权威文档/产品范围/数据会计/安全/架构/运行/测试供应链/UX/综合裁决 | 每个 Gate 合并前跑对应专项 + DD7；大版本全量 |
| 触发式 | 数据扩张前 DD3+性能；内部工作台前 DD2+DD3+DD4+合规；竞对矩阵季度（2026-12）；竞对清单半年（2027-03） | 见尽调总汇 §3 |

## 4. 优化改进候选（非任务批准）

三来源整合（竞品清单 35 条、O-01~O-17、MCP 补充 S-1~S-6）分组 A–F 与推荐排序见[整合优化方案](docs/80_reviews/2026-09-15-integrated-optimization-program.md)。任何条目进入执行须经 CURRENT_ROADMAP 按 D053 裁决。

## 5. To-do List 状态（2026-09-15 收敛）

| ID | 内容 | 状态 |
|---|---|---|
| T00–T08 | 基线核对 → R2 → R3 → R4 → S01 关闭 | **completed**（台账 §7/§9，main 全绿） |
| T09 | C 级出口协议 + L0/L1 基准 | **协议与基准交付**；出口 PASS 待 A1–A3 人工项 + A4 |
| T10 | 溯源/重述/MCP/起草四子包 | **completed**（B3/B4/B5/B6 全部落地） |
| T11 | 性能基线（G2） | **completed**；数据扩张（C1）**blocked on A4** |
| T12 | 问数 v1 + 评测集 | **completed**（确定性 v1，100% 命中）；LLM 通道 **gated on A5** |
| T13 | 内部工作台 | **blocked**：C 级出口 PASS + 数据授权 |
| T14 | U4 oracle / rnd_exp / U9·O5 / U10 | **blocked**：外部材料与授权 |

## 6. 单一 Agent 工作协议

1. 一个 Gate 一个 `codex/` 分支/独立 worktree；不压成一个提交。
2. 每个 Gate 均执行：读取批准规格 → 写红灯测试 → 最小实现 → 目标测试 → 全链测试 → 独立规格审查 → 代码质量审查 → 提交推送 → 等同 SHA CI。
3. 不整包 cherry-pick 旧 Sol/Kimi/GLM 候选；需要时只把它们当作调查材料，按当前规格重做。
4. 禁止用 skip/xfail/弱化断言/删除测试/关闭认证/`curl -k` 换绿色。
5. 代码、生成契约、运行证据、文档分别如实提交，提交标题不能用 docs/chore 掩盖业务代码。
6. 修改安全、迁移、对象存储或发布事务前，先核对批准规格；规格有歧义就暂停该点，不自行创造宽松语义。
7. 只承认目标 commit 与 CI head SHA 完全一致且 required jobs 全 success、无 skip 的结果。
8. 完整任务结束后提交并推送；只暂存本任务文件，不带入其他会话的未跟踪或未提交内容。

## 7. 已踩过的坑与停机条件

- 多个 Agent 共用检出、后台 pull/push 会造成基线错乱；后续禁止。
- 旧分支局部绿色不能替代当前主线同 SHA 全绿；审查报告也必须注明快照时点。
- HTTP GET 不等于只读，冻结/发布等隐藏写必须按副作用保护。
- 数据库有表不等于审计已闭环；必须覆盖 401、403、allow、写入失败和保留策略。
- 对象存储、数据库和审计是跨边界事务，不能在 route 末尾补一条日志冒充原子性。
- 文档新增也会让 CI 变红；**远端门禁现为 m6**（含链接/兼容/读者测试）——提交前本地跑 m6。
- 发现第二迁移头、跨企业可访问、AI 可发布/自批、恢复 hash 不一致、测试 skip、目标 SHA 与 CI SHA 不同，立即停止关闭流程。
- 本会话新增坑见 §2.4（checkout 正则、tail 吞退出码、minio 漂移、§3.3 身份横切、裸连接 entity select 等）。

## 8. 下一位 Agent 的第一条动作

从当前最新 `origin/main` 做会话开始三核对（PROJECT_STATE / git log / CI 状态），确认无新外部提交后按 §2.3 顺序领取：**先接 10 条人工查源结果修抽取 YAML**（若用户已完成翻页核对），或先执行 AI 交叉评调度（若用户已运行评审会话）。不要先做 UI 大改、行业扩张决策或任何 T13 内容。

当前对外状态统一表述为：**U8 closed；S01 completed；T09–T12 基础交付完成；C 级出口 Go/No-Go 前置仅剩人工三件套 + A4 材料；T13/T14 等外部。**
