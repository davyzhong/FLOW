---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目尽调、优化与单 Agent 执行总交接
doc_type: navigation
status: current
version: 3.5
created_at: 2026-09-12
updated_at: 2026-09-25
owner: FLOW
applies_to: repository
---

# FLOW 项目尽调、优化与单 Agent 执行总交接｜2026-09-25

> 本页是下一位单一 Agent 的工作入口，整合了多 Agent 执行审计、R1 修复复核、竞品与方法论研究、工程收口计划和后续产品优化建议。它负责说明“现在在哪里、还要查什么、先改什么、怎样证明完成”；项目状态仍以 [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md) 为唯一事实源，任务顺序仍以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为唯一执行入口。

## 0. 执行摘要

### 0.1 当前可信结论

- **当前基线：`main@a461b54`**（2026-09-19 晨，全 job CI 绿）；本会话（09-17～09-19 连续执行）交付批次终点链 `5442d9c`→`0c4c45a`→`9cf8cb3`→`02c11ea`→`0af6a8a`→`a461b54`。
- **S01 / U8 关闭不变**；阶段 3 基础（T09–T12）与 C 级出口执行批次交付不变（台账 §8/§9）。
- **指标库 v1.2 行业参考包已交付**（借鉴 #21：16 行业 + 流动资产率 + 基准增强，`5442d9c`）；**O-01/O-02（AI 问数 v2 地基）已落地**（语义上下文端点 + 提议→复算管线，`3a0ee20`）。
- **前端一致性整改计划 Task 0–9 全部关闭**（P3–P5 批次：metric-library/investigations 深度迁移、状态门禁 frontend-states.spec、60 图状态矩阵归档；门禁矩阵 = 一致性 10 路由 + 溢出 11×3 视口 + 状态 5×3 + 导航/边界 = 69 项，全跑生产构建）。
- **后端既有 flake 修复并 CI 实证**：objective freeze 幂等的行序漂移（`0af6a8a`，publishing-golden 绿）。
- **数据来源政策已由用户明确（2026-09-19）**：无私有数据来源，研发期一律网络公开来源数据——A4「等待外部财报材料」的前提作废，数据扩张改为继续走公开财报抓取管线（见 §2.2/§2.3）。
- 多 Agent 并行已终止，单一 Agent、逐 Gate、串行执行不变；产品战略方向不变（经分专员工作台，公开财报独立先行）。
- **下一里程碑不变 = C 级出口 Go/No-Go 裁决**；前置人工项不变（见 §2.2）。
- **大麦物流两年 synthetic 演示数据全链已交付并关闭（2026-09-24～25 批次，分支 `codex/damai-logistics-implementation`）**：计划 v2.4 串行 A1–A4 → B1–B3 → C1–C3 全部完成，提交链 `ece11d2`→`4950e73`→`1052ea6`→`5c2c4d4`→`0bb27d8`→`c1c5a20`→`ff3b828`→`1d3f757`→`8b61bec`→`3e20628`→`082b0eb`→`f867842`→`307300b`→`077d35c`→`d701c1d`→`75fb2f1`（completed 状态翻转）；实测 verify 19/19、八页面 E2E 9/9、二次 seed 全表零增长、发行包零漂移；C3 全量回归 17 门禁绿。CI 验收：active 收尾 head `d701c1d` 全绿（run 36098674773）；最终 completed SHA `75fb2f1` 17 jobs 全绿（run 36101860056；metrics-known-answers 首跑因 Docker Hub 拉取被 connection reset 瞬断失败，`--failed` 重跑即绿，纯网络 flake）。详见 §2.5。

### 0.2 当前最重要的偏差与缺口

| 类型 | 当前判断 | 处理方式 |
|---|---|---|
| 10 条抽取错误候选 | BABA NCI 8 条 + JDL 现金流 2 行，值在源 PDF 文本层不存在（压力测试实锤） | 人工翻页查源（压力测试报告 §2 清单）→ 修抽取 YAML 新版本 → 重跑基准 |
| C 级出口 PASS | 证据链就绪，缺独立盲评与 holdout 执行 | 用户执行 AI 交叉评（包已备）+ 抽签 |
| 数据扩张 | **政策已更新**：无私有数据线，公开网络数据是研发期唯一来源 | 走既有公开财报抓取管线（harvest/港交所）扩充，不再等待 A4 外部材料 |
| 溯源真实来源链接 | 原卡「私有 PDF 如何经 API 供给」决策——**已被公开数据政策解开** | 按公开 URL/公开文件引用设计落地（下一个可领取项） |
| AI 问数 LLM 通道 | 用户裁决另行 | 保持 gated；O-01/O-02 地基已就绪 |
| F-ExportAudit | 用户明示暂不管；现有描述「补审计行」规格不足 | 搁置；领取前先补规格 |
| 合规尽调 G4 | 未启动 | A5；阻塞 T13 与 MCP/LLM 开放 |

## 1. 权威关系与阅读顺序

下一位 Agent 开始工作时按以下顺序读取，禁止从历史聊天或旧三 Agent 计划直接领任务：

1. [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md)：唯一 current state；
2. [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md)：唯一可领取路线图；
3. [S01 工作包](docs/50_plans/work_items/S01--post-u8-boundary-contract-security.md)（completed）与 [C 级出口工作包](docs/50_plans/work_items/PUBLIC--c-level-exit-protocol.md)（当前 Gate，含 §3.7 出口裁决参数）；
4. [战略重构设计 V1.1](docs/superpowers/specs/2026-09-13-flow-strategic-reset-design.md)、[PRODUCT_SCOPE](docs/20_product/PRODUCT_SCOPE.md)、[PRODUCT_PRINCIPLES](docs/20_product/PRODUCT_PRINCIPLES.md)：产品目标、固定原则和冲突裁决；
5. [协调台账](docs/70_operations/2026-09-14-coordination-ledger-glm.md) §6–§9：R0/R1、R2/R3/R4、T09–T12、C 级出口执行批次的完成证据；
6. [前端一致性整改计划](docs/superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md) §10 执行日志：P0–P5 批次全记录（已关闭）；
7. [竞品优化清单](docs/competitive/optimization-checklist.md)、[知识库 O-01～O-17](docs/knowledge-base/09_competitive/2026-09-14-optimization-backlog.md)、[五维矩阵](docs/competitive/2026-09-17-five-dimension-matrix.md)：候选需求证据（O-01/O-02 已落地地基）。

冲突裁决顺序：用户最新明确指令 → 已接受决策 D052–D054 → approved 规格 → PROJECT_STATE → CURRENT_ROADMAP / 当前工作包 → 本交接 → review / research → 历史计划和聊天记录。

## 2. 本会话（2026-09-17～09-19 连续执行批次）交接明细

### 2.1 已完成（全部推送 main，尖端 CI 全 job 绿）

| 批次 | 内容 | main 锚点 |
|---|---|---|
| 指标库行业包 v1.2 | 借鉴 #21 落地：16 行业参考包（经营指标目录=对标参考，financial_reference 只登记素材真实值）+ 通用指标新增流动资产率 + 基准增强（现金流量比率≥1、产权比率 100%/200%）；**v1_1.yaml 是派生产物——改动走 finalize 脚本再生成（已幂等化+修 derived_from 炸字符 bug）**；前端新增「行业参考包」tab | `5442d9c` |
| O-01/O-02 地基 | `GET /metric-library/semantic-context`（四元素投影，引用携带 entry_id 回链口径）+ `POST /metric-library/computation-proposals`（治理字典提名→确定性 Decimal 沙盒复算，缺口=结构化 refusal）+ `GET /computation-inventory`；零 RBAC 矩阵变更；路由清单 66→69 | `3a0ee20`/`c93c1f1` |
| P4 metric-library 迁移 | PageState/flow-btn/flow-table 收编；裸色 63→7（金棕对比对固化为文件作用域 token）；CSS 871→780 行 | `0c4c45a` |
| P5-A investigations 详情 | 四类非加载态迁 PageState（h1 稳定）、7 按钮迁 flow-btn；证据工作台专用色板按完成标准保留 | `b7b4257` |
| P5-B Task 8 切片 | dashboard 重试按钮、四问工作台 flow-error/flow-field；public/internal 落地页审计免迁 | `3089472` |
| P5-C1 状态门禁 | frontend-states.spec：5 路由×{加载/503/403} 结构断言（h1 稳定、role 语义、中文文案、重试）；**抓到两真缺口并修复**：operations-overview 无加载态、Next RouteAnnouncer 占 role=alert（断言收窄 main） | `9cf8cb3` |
| P5-C2 矩阵归档 | 60 图（4 数据密集页×5 态×3 视口）+ 索引册入 docs/assets/screenshots/state-matrix/；生成器按需触发（FLOW_STATE_MATRIX_ARCHIVE=1） | `02c11ea`/`a461b54` |
| 后端 flake 修复 | objective freeze 幂等：created_at 事务时间戳致排序键打平+无序查询行序漂移→payload 哈希不稳；tie-break 补 uuid7 主键；CI publishing-golden 实证绿 | `0af6a8a` |
| 并行会话 | 竞对五维矩阵、知识库第二截面增量扫描（#20–#24）、roadmap v1.7 | `7717102`/`4cb2535` 等 |

### 2.2 卡住的问题（外部/人工依赖为主）

1. **10 条抽取错误候选人工查源**：清单在 `docs/60_delivery/2026-09-15-cainiao-stress-test-report.md` §2；需人翻 PDF 后修抽取 YAML 并重跑基准。
2. **AI 交叉评执行**：包已备（`docs/80_reviews/ai-cross-review/README.md`），需用户开非 GLM 会话执行——实现方不得自评。
3. **溯源真实来源链接**：决策已被公开数据政策解开，**不再是卡点，转为下一步可领取项**（按公开 URL/文件引用设计，与溯源浮层 pointer-events 联动）。
4. **AI 问数 LLM 通道**：gated（用户另行裁决）；O-01/O-02 地基已就绪。
5. **F-ExportAudit**：用户明示搁置；领取前先补规格。
6. **合规尽调 G4 / U4 oracle / rnd_exp 原文 / U9·O5 / U10**：外部材料与授权，同前不变。
7. **infra 小项**：web 容器 healthcheck busybox wget 假阴（Node 实测健康）——compose 修复方案在册待用户批准（红线）；常驻栈已刷新至 `a461b54` 并实测 200。

### 2.3 下一步计划（下一 Agent 按序领取）

1. **溯源真实来源链接**（已解锁）：按公开来源设计——statement 溯源行项目回链公开财报 URL/公开文件引用 + 前端浮层跳转（与既有 ProvenanceBadge/ProvenanceHover 联动）；先补半页设计输入再动工；
2. **公开数据扩张**（政策更新后改为可领取）：按既有 harvest 管线扩公开财报公司面 → 抽取 → L0/L1 基准 → 冻结 → 重述链实战验证（原 A4 批次流程，来源改公开渠道）；
3. 收到 10 条人工查源结果 → 修抽取 YAML → 重跑双层基准 → 更新压力测试报告；
4. 用户执行 AI 交叉评后逐条归因写 adjudication；三项齐备 → **C 级出口 Go/No-Go 裁决** → 解锁 T13（需 A5）与 T12 LLM 通道；
5. 同步纪律：每步完成即更新路线图/台账/PROJECT_STATE 并同 SHA CI 全绿。

### 2.4 本会话踩过的坑（新增，接续 §7）

- **`metric_dictionary_v1_1.yaml` 是派生产物**：手改会被 `finalize_metric_dictionary_v1_1.py` 再生成清掉——改动必须编码进脚本（NEW_METRICS/BENCHMARK_UPDATES/INDUSTRY_PACKS + 幂等 DECISION_NOTES）再运行；已验证再生成零漂移且幂等；
- **YAML 值内 ` #` 触发注释截断**：`借鉴 #21` 前的空格让标量静默截断甚至解析报错——含 # 的 provenance 一律单引号包裹（既有先例）；
- **本地 dev DB 是 `_db_payload` 的过滤权威**：YAML 加条目后本地测试会拿旧计数（假红），须按 conftest 同款 env 跑 `import_all` 幂等重导；CI 无 DB 走 YAML fallback 不受影响；字典升级后 api 容器镜像必须重建（`make stack-up`）；
- **指标计数多点锁定**：改条目数必须全仓 grep 计数断言（test_metric_library_api **和** test_metric_library_store 两处，后者漏改被 CI integration 抓包）——「受影响套件」直觉清单不可靠；
- **门禁前 pkill 必须按进程名 `pkill -f next-server`**：`pkill -f "next start"` 杀不到改名后的 next-server（残留 5 个实例曾让门禁挂 30 分钟无输出）；
- **Next.js RouteAnnouncer 本身是 role=alert**：页面级 alert 断言必须收窄 `main [role=alert]`，否则 strict mode 双元素冲突；403 文案存在两套既定措辞（STATUS_TEXT「授权拒绝」与 operations-overview「没有访问权限」），门禁接受两套；
- **user-closure CI flake 判定标准 = 同提交本地绿**：CI 连挂三次（清洗超时）vs 本地官方脚本 4/4 全绿 14.2s——直接 `gh run rerun --failed`，不要因「连挂」误判回归去翻代码；
- **objective freeze 的 created_at 是事务时间戳**（server now()，同批插入全同）：排序键必打平，无 ORDER BY 查询的物理序漂移会破坏「同内容同版本」幂等——凡进 payload 的行序必须补 uuid7 主键 tie-break；
- **docs/ 下新增任何 .md（含 assets 索引册）必须带 frontmatter**，提交后重跑 check_docs m1+m6；生成的索引册要把 frontmatter 写进生成模板，否则再生成即丢；
- **workflow 内重跑官方脚本前先看常驻栈**：docker daemon 被用户关闭会让 DB-backed 测试全数 connection error，属环境不在线而非回归。

### 2.5 大麦批次交接（2026-09-24～09-25，分支 `codex/damai-logistics-implementation`）

- **完成证据**：verify 19/19（`make damai-demo-verify`）；八页面真实 E2E 9/9（`make test-damai-demo-e2e`，隔离栈 + Playwright，38s）；数据合同 8/8（含二次 seed 计数零增长）；U8 非破坏升级验证全链 PASS（dump SHA 核对 + 恢复 11 财报 + 升级 0029 + HTTPS 三方对账，证据 `work/s01-verification`）；M6 文档门禁绿（278 docs, 0 errors）。
- **数据实测**：24 个月（FY2025–FY2026）、1920 经营实际 / 10752 预算 / 4800 AR / 672 财务实际、4 客群 / 40 客户 / 8 产品 / 6 区域 / 5 组织；指标覆盖 FY2025 22/40、FY2026 25/40（来源 `fixtures/damai/manifest.json` 与覆盖包）。
- **红灯抓出并修复的真实缺陷**：reports-center 两个发布 fetch 缺 `Idempotency-Key`（§7.1 合同）+ Next 代理丢弃该头——已修并补单测。
- **一键恢复**：`make damai-demo-up`（构建发行包 → 迁移 → seed → verify）；分步 `damai-demo-build/seed/verify`。
- **已知限制**：dashboard 总量域 OCF actual 不存在是合同真相（state=degraded 为预期）；合成数据不解除公开 C 级与真实企业门禁；迁移头 0029（worktree 链），主工作区共享库在 0030，严禁混用。
- **新坑**：macOS Docker 无 host 网络，建 MinIO 桶须 `--network container:flow-minio-1`；`compose up -d --wait` 会误判一次性 init 容器 exit(0) 为失败；`down -v` 偶发只删网络须跑两次；**回归驱动运行期间严禁并行手动跑同库测试**（并发污染曾致 report_snapshot 计数假漂移，安静环境复跑全绿证伪）；测试 conftest 默认指向共享 `flow` 库（迁移头 0030），本 worktree 跑测试必须显式导出划痕库 env。
- **C3 回归抓出并已修复的四个真实缺陷**（CI 全绿于 `d701c1d`，run 36098674773）：①发布服务冻结视图无粒度过滤导致二次 seed 冻结内容漂移（`082b0eb`，修复=按 snapshot.as_of_period + 五维度 IS NULL + ORDER BY id）；②集成测试清库顺序缺分析链模型致 RESTRICT FK 卡死、对象存储测试裸 boto3 被系统代理挂死（`f867842`）；③quay.io/minio 组织私有化 + Docker Hub minio 下架，compose 镜像全部不可拉，换 `bitnamilegacy/minio` 并补全路径 entrypoint/healthcheck（`307300b`）；④data-contract/intake-e2e 撞 20 分钟 `timeout-minutes`，提到 40，且注释必须独立行（`077d35c`+`d701c1d`，test_ci_gate_inventory 用行尾锚正则）。

## 3. 完整尽调计划（触发条件与频率不变）

| ID | 尽调包 | 触发 |
|---|---|---|
| DD0 | 基线冻结与证据盘点 | 每次会话开始（轻量版） |
| DD1–DD9 | 权威文档/产品范围/数据会计/安全/架构/运行/测试供应链/UX/综合裁决 | 每个 Gate 合并前跑对应专项 + DD7；大版本全量 |
| 触发式 | 数据扩张前 DD3+性能；内部工作台前 DD2+DD3+DD4+合规；竞对矩阵季度（2026-12）；竞对清单半年（2027-03） | 见尽调总汇 §3 |

## 4. 优化改进候选（非任务批准）

三来源整合（竞品清单 35 条、O-01~O-17、MCP 补充 S-1~S-6）分组 A–F 与推荐排序见[整合优化方案](docs/80_reviews/2026-09-15-integrated-optimization-program.md)。任何条目进入执行须经 CURRENT_ROADMAP 按 D053 裁决。**O-01/O-02 已落地地基（本会话）**；五维矩阵结论=主线不调整，AI 问数 v2 必须项即 O-01/O-02 全量（任意 AST 提议与 LLM 通道另行裁决）。

## 5. To-do List 状态（2026-09-19 更新）

| ID | 内容 | 状态 |
|---|---|---|
| T00–T08 | 基线核对 → R2 → R3 → R4 → S01 关闭 | **completed**（台账 §7/§9） |
| T09 | C 级出口协议 + L0/L1 基准 | **协议与基准交付**；出口 PASS 待人工三件套 |
| T10 | 溯源/重述/MCP/起草四子包 | **completed**；真实来源链接按公开来源设计**可领取** |
| T11 | 性能基线（G2） | **completed**；数据扩张（C1）**改道公开管线**（政策更新） |
| T12 | 问数 v1 + 评测集 | **completed**；**O-01/O-02 地基已交付**；LLM 通道 **gated on A5/用户裁决** |
| T13 | 内部工作台 | **blocked**：C 级出口 PASS + 数据授权 |
| T14 | U4 oracle / rnd_exp / U9·O5 / U10 | **blocked**：外部材料与授权 |
| FE | 前端一致性整改 Task 0–9 | **completed**（P0–P5 全批次，计划 §10 日志）；F-ExportAudit 搁置待补规格 |

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
- 文档新增也会让 CI 变红；**远端门禁现为 m6**——提交前本地跑 m1+m6（本会话 state-matrix README 再证：assets 下的索引册也在门禁射程内）。
- 发现第二迁移头、跨企业可访问、AI 可发布/自批、恢复 hash 不一致、测试 skip、目标 SHA 与 CI SHA 不同，立即停止关闭流程。
- 本会话新增坑见 §2.4（派生 YAML、# 注释截断、dev DB 过滤权威、计数多点锁定、next-server pkill、RouteAnnouncer alert、user-closure flake 判定、freeze 事务时间戳等）。

## 8. 下一位 Agent 的第一条动作

从当前最新 `origin/main`（`a461b54` 或更新）做会话开始三核对（PROJECT_STATE / git log / CI 状态），确认无新外部提交后按 §2.3 顺序领取：**首选溯源真实来源链接（公开来源方案，已解锁）或公开数据管线扩张**；若用户已交付人工三件套产出（查源结果 / AI 交叉评结论），优先接手归因与抽取 YAML 修订。不要先做 T13 内容或任何等待 A5 的开放面。

当前对外状态统一表述为：**U8 closed；S01 completed；T09–T12 基础交付完成 + O-01/O-02 地基交付；前端一致性整改 Task 0–9 关闭；大麦两年 synthetic 演示数据全链交付并 completed（分支 `codex/damai-logistics-implementation`，最终 SHA `75fb2f1` CI 17 jobs 全绿，run 36101860056，待合入 main）；C 级出口 Go/No-Go 前置仅剩人工三件套；数据扩张按公开管线推进（2026-09-19 政策）；T13/T14 等外部。**
