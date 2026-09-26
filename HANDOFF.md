---
doc_id: FLOW-HANDOFF-STRATEGY-20260912
title: FLOW 项目尽调、优化与单 Agent 执行总交接
doc_type: navigation
status: current
version: 4.3
created_at: 2026-09-12
updated_at: 2026-09-27
owner: FLOW
applies_to: repository
---

# FLOW 项目尽调、优化与单 Agent 执行总交接｜2026-09-27

> 本页是下一位单一 Agent 的工作入口，整合了多 Agent 执行审计、R1 修复复核、竞品与方法论研究、工程收口计划和后续产品优化建议。它负责说明“现在在哪里、还要查什么、先改什么、怎样证明完成”；项目状态仍以 [PROJECT_STATE](docs/00_start_here/PROJECT_STATE.md) 为唯一事实源，任务顺序仍以 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 为唯一执行入口。

## 0.4 夜间接手执行手册（2026-09-27，当前权威）

> **本节覆盖本文其余旧会话交接快照。** 旧章节保留历史证据，不可据其旧顺序领取任务。下一位 Agent 开始前先从 GitHub 同步 `main`，再读 `AGENTS.md`、`docs/00_start_here/PROJECT_STATE.md`、`docs/50_plans/CURRENT_ROADMAP.md` 和相应工作包。唯一任务顺序是路线图中的 11 项队列；本节只是对同一队列逐项提供执行手册，不构成第二条队列。

### 接手基线、当前状态与操作纪律

- 本次状态同步开始时已推送主线为 `b98844ad`（包含交接规则和上一版状态快照）；`gh run list --commit b98844ad` 未发现 CI run。实际应用/数据包代码基线为 `fc6e63a7`：包含 `9729dbc4` ORG-LEDGER 工作包、`880f1b76` 三表 schema 提案、`e1a4d264` 大麦企业包基础，以及 `fc6e63a7` 对具体 schema 的批准记录和 README 元数据修正。接手时必须重新核对最新 main 和同 SHA CI，不得沿用旧 SHA 的绿灯。下一位 Agent 开始前执行 `git pull --ff-only` 并核对当前 dirty changes，不要为了“clean”丢弃代码草案。
- 文档门禁现状：在当前基线 `fc6e63a7` 上，本次本地重跑 `python3 scripts/check_docs.py --phase m1` 为 PASS（297 docs、89 legacy-exempt、0 errors）；`plan_views.py --check`、链接检查和 `git diff --check` 均 PASS。`python3 scripts/build_enterprise_data_package.py verify` 同样 PASS（25 个登记文件）。这些是当前本地结果，不代表未来交接提交的 CI；仍需在交接提交后核同 SHA CI。
- 路线图队列：11 项；本次最新盘点为已完成 0、实际执行中 0、队首待续 1、排队 9、外部材料受限 1。唯一队首为 ORG-LEDGER；先前观察到的 `uv run pytest -q tests/fixtures/test_damai_loader.py` 进程已结束，但其退出码/日志未从发起终端回收。队列顺序和每次状态变化只更新 `CURRENT_ROADMAP.md`；每完成一项，补验收证据、更新工作包/`PROJECT_STATE.md`，提交并立即推送后才进入下一项。
- 只在 `main` 上做，禁止新建并行任务分支；不得同时开始下一项。用户已授权常规项目实施与验证，不再为日常测试、分析、文档或常规实现请求再次批准。既有全局安全红线仍有效：真实数据迁移/schema、删除/覆盖/恢复常驻库、密钥/CI 配置、公开部署等按 `AGENTS.md` 处理；尤其常驻 `flow` 中的测试批次偏差 `01a0dcdd-8245-7c17-99aa-fce91a8a7a57` 不得自行删除、回滚或切 latest。
- **状态口径**：`进行中`=此刻确实有命令、审查或实现正在执行；`队首待启动`=当前第一项但未开工；`排队`=严格等待前项完成；`外部材料受限`=先按本手册执行主动恢复和替代方案，不是停工态。工作包 frontmatter 的 `active/blocked` 表示工作包生命周期或验收门槛，不覆盖路线图执行状态。
- **ORG-LEDGER 的最新事实与安全边界**：工作包由 `9729dbc4`、具体三表 schema 提案由 `880f1b76` 推送；用户批准该准确方案由 `fc6e63a7` 记录。批准仅覆盖工作包列出的三表与对应迁移，不覆盖额外 schema、认证/RBAC 改造，也不授权在共享/常驻 DB 清理/初始化。可执行已批准迁移，但只在隔离数据库验证；不要对常驻库迁移或写入。
- **发行包基础和当前未提交实现草案**：`e1a4d264` 已将 `data/enterprise/damai-logistics/v1/` 下27个包文件及 `scripts/build_enterprise_data_package.py` 一并推送到 main（该提交新增28个文件）；不要重复生成或重建同名目录。`fc6e63a7` 后只读运行 `python3 scripts/build_enterprise_data_package.py verify` 得到 exit 0：manifest 登记的25个文件 SHA/JSONL 行数通过，样例为8个组织单元、8个岗位、8个身份、142条权限映射。此自检**不等于工作包验收**：仍需验证 build 幂等、manifest 覆盖、恶意/缺项拒绝、合成/凭据字段安全、RBAC 映射、业务引用及 full/business 初始化。当前 dirty worktree 已出现 `models/__init__.py` 修改、`infrastructure/models/enterprise_directory.py`、`flow_api/enterprise/directory.py`、迁移 `0031_enterprise_directory.py`、`tests/enterprise/test_org_directory_models.py` 与 `test_directory_sync.py`，以及 `fixtures/damai/loader.py` 修改；不得覆盖、重置、擅自暂存或断言已通过。先前 `uv run pytest -q tests/fixtures/test_damai_loader.py` 进程现已结束，但结果未回收；接手者先从原终端回收，否则在审阅代码后重跑，再对照获批 DDL 继续。
- **遇到失败的统一处理**：保留原始日志和失败产物 → 定位根因并判别代码/数据/环境/外部输入 → 先运行最小重现 → 做最小修复或有记录的替代验证 → 重跑原失败项及相邻回归。禁止删断言、改预期值迎合实现、重写原始 oracle、用 synthetic 结果冒充真实验收。若原验收客观上不可完成，交付可复现的调查、替代结果、未满足项与重启条件；不能声称原验收通过。
- **每项汇报格式**：完整 11 项队列和计数；当前项与细分步骤；本轮完成证据（SHA、命令、结果）；实际问题/替代路径；下一项何时解锁和唯一下一动作。不要写“等待用户验证/批准”作为常规动作；只有触及明文安全红线的 schema 执行边界才须记录为精确批准门。

### 唯一串行 To-do 的逐项操作卡

每张卡的“完成后”是唯一可进入下一项的条件。若发现路线图与证据不一致，先核对主线提交/原始证据，更新路线图并通过文档门禁，再按更正后的顺序工作。

#### 1. 企业组织建制与经营账套初始化包（唯一队首）

**入口材料：** `docs/50_plans/work_items/ORG-LEDGER--enterprise-initialization-package.md`、`docs/50_plans/work_items/DAMAI--full-year-demo.md`、`docs/50_plans/CURRENT_ROADMAP.md`、`docs/20_product/` 中 enterprise/RBAC/导入发布相关规则，以及 `services/api/src/flow_api/fixtures/damai/loader.py`、`scripts/seed_damai_demo.py` 和 `fixtures/damai/`。

**授权边界：** 用户已批准发行包行为：完整初始化同步组织并重建业务、业务重置保留组织、仅作用于 manifest 指定企业；包格式/SQL/初始化入口均可实施。具体三表 schema 和对应 Alembic 迁移的批准已记录在 `fc6e63a7`，可以实现并在隔离数据库验证；不得扩展为其他表、认证/RBAC 变化，禁止对常驻开发库迁移、清理或初始化。

**操作步骤：**

1. 开始先拉取 `main`、核实分支/HEAD/远端与同 SHA CI；逐项读取上述工作包/规则，检查当前数据库迁移头、企业/RoleBinding 模型、对象存储引用方式和 seed 实际副作用。基于 `e1a4d264` 只读审查现有发行包与校验器，核对 manifest 登记25文件为何不含 README/manifest、对现有完整发行目录的覆盖、来源 SHA、字段/引用/重复项与脚本写入面，再建立本任务内部子步骤状态表，只在 HANDOFF/路线图的当前任务栏报告，不新建第二条队列。
2. 盘点 `fixtures/damai/` 的 canonical JSONL、报表、预算、运营侧车、来源文件和 manifest；记录文件数、行数、SHA、来源与可复用路径。目标发行目录按工作包 `data/enterprise/damai-logistics/v1/` 设计；复用现有 canonical 真相，不能复制出两份可手工编辑的数据。
3. 固定 manifest 合同：企业稳定 code、包/模块版本、synthetic 标记、全局依赖版本、组织/业务稳定键、引用关系、每个文件 SHA/行数、校验规则及允许的数据清理范围。先写 manifest/schema 测试，再实现纯文件 validator。测试应覆盖缺文件/错 SHA/错行数/版本不匹配/非 synthetic/重复 code/断裂引用/跨企业引用/未知角色/含 credential 或敏感个人字段等拒绝路径。
4. 组织数据只使用明确虚构人员、`example.invalid` 邮箱、保留号段电话、无凭据 actor ID；组织、岗位、成员 ID 带企业命名空间。权限文件仅表达期望映射，必须限制在现有 Role/Action 合同内；不可借 seed 绕过 Principal/RBAC，也不可制造可登录密码、token 或真实身份信息。
5. schema 已获批准：对照工作包提案审查当前 migration/model/test 草案是否严格实现三表与约束，先跑纯模型/迁移单测与负向测试；若代码超出批准范围则收窄回批准 DDL，不可自行加表/改 RBAC。数据库验证只在隔离 PostgreSQL 栈执行。
6. 列出逐表 business reset ownership/lineage 清单，证明只删除 manifest 企业记录。不得 `TRUNCATE`、`DROP SCHEMA`、全库 delete；保留审计事件、全局字典、共享对象及被其他企业引用的对象。`full` 与 `business` 两种动作都须事务化，完整失败能回滚到无部分写入状态。
7. 创建/检查初始化入口：preflight 校验数据库版本与企业存在，组织同步遵循停用而非删除历史主体，业务 seed 复用领域服务完成 Intake→Review→Snapshot→Analysis→Freeze。SQL 和服务 seed 必须由同一 manifest 导出或校验，避免双重真相；不添加交互式人员/口径选择，也不偷偷自动备份。
8. 仅在隔离 PostgreSQL + MinIO 栈做首次 full、重复 full、business-only 重置、坏包拒绝、注入中途失败回滚、目标企业隔离、组织保留/同步、对象共享保护、审计追加保留。确认 seed 幂等、失败无半写、非目标企业与全局配置不变。
9. 回归原有大麦交付：`make damai-demo-build`、verify 19/19、业务页面 E2E 9/9（按仓库现行命令和版本复核），再跑 API/Web/合同/文档门禁及同 SHA CI。修复 README 的 M1 `doc_type` 问题并确认 frontmatter 门禁通过。保存栈配置、数据库隔离证明、对象清单、行数与 SHA、完整命令/退出码；常驻 `flow` 前后只读核对且不得被测试改动。
10. 更新发行包 README、ORG 工作包、`PROJECT_STATE.md`、本 HANDOFF 当前快照及路线图证据；只有原验收全部满足才标 completed。提交前检查 `git diff --check`、`python3 scripts/check_docs.py --phase m1`、链接/契约/相关测试；只暂存本项文件，按 conventional commit，随后立即 `git push origin main` 并查询该 SHA CI。

**验收：** 单一命令可 full 初始化和 business-only 重置；数据包可移植、可复验、版本/哈希/来源齐备；组织同步/保留符合语义；所有企业边界、审计、共享对象、失败回滚及幂等性测试通过；旧大麦 verify 19/19、E2E 9/9 不回退；文档门禁和同 SHA CI 全绿。迁移与任何破坏性验证仅在隔离栈进行。

**遇到问题：** manifest 与现有 fixture 不一致时以现行 canonical 资产为起点，先解释差异并保留原文件，不手改派生产物；删除范围不能证明企业归属时拒绝删除，补 ownership/lineage 或用安全重建策略；共享对象引用不清时保留对象；seed 如会写常驻库则停用该路径并构建隔离栈；测试环境失败先检查 `flow_test`、compose project 名和 MinIO bucket 初始化，不清空常驻数据；schema 方案如出现额外表/RBAC 改动，先补具体方案和批准，不在实现中扩范围。

**完成后：** 才进入第 2 项 UX 可见性与全站验收关闭。

#### 2. UX 可见性与全站验收关闭

**入口材料：** `docs/50_plans/work_items/UX--post-damai-experience-closeout.md`、`docs/50_plans/2026-09-26-ui-deep-link-implementation-plan.md`、`docs/60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md`、`docs/80_reviews/2026-09-26-ui-linkability-audit.md`。深链批次一至三已完成；批次三代码锚点 `cef0c362`，全量 API 845、生产 E2E 93/93、Web 142/142、脚本 101/101；隔离大麦 verify 19/19、只读 GET 43/43、浏览器 9/9。不要重复做已完成批次。

**操作步骤：**

1. 在当前干净 `main` 上建立 Gate 1 覆盖总表：每条路由列出方法与参数、公司/期间/批次、API 端点、来源事实、环境、SHA、响应/内容摘要、UI状态、视口和归因。先核对已有 43 条只读 GET 清单；只补未覆盖路由，不重新探测已有项。
2. 对每个数据页逐条比对 API 与真实页面：当前已发布值、未发布、无源事实、不适用、权限不足、错误、加载中、部分降级。缺值按源事实/映射/计算/快照/筛选/前端消费/设计排除归因，严禁简单写“无数据”。
3. 在 390/1024/1440 宽度验页面与状态；保存可复验的 E2E/截图摘要（按项目既有截图矩阵约定存放），补测试前先做 TDD。优先关掉有事实支持且影响页面呈现的缺口，禁止为了“填满”而补零或伪造数值。
4. 对所有目标 KPI、趋势、矩阵、报告和 Finding 检查真实下钻目标。深链批次已交付的入口只回归验证，不重做。检查 actor/enterprise 隔离和数据工作台批次可见性。
5. **只读安全：** 以下 GET 会 freeze/写入快照，不能当作只读探测调用：`/api/v1/statements/{report_id}/objective-snapshot`、`/api/v1/statements/{report_id}/objective-snapshot/html`、`/api/v1/operations/overview/{report_id}/{html|xlsx|pptx|pdf}`。欲验证其行为，先代码审查副作用，再只在隔离数据库/对象存储测试，不能对常驻 `flow` 或用户环境探测。
6. 完成 Gate 5：依次运行 `make damai-demo-build`、安全隔离的 dashboard 测试（确认脚本目标为 `flow_test`）、`make test-damai-demo-e2e`、`make lint && make typecheck && make test-web`、`python3 scripts/check_docs.py --phase m1`、`python3 scripts/documentation/links.py --check`、`scripts/check_contracts.sh`；涉及 API 全量变更时再运行 `cd services/api && uv run pytest -q`。最后核对最新提交 SHA 的 GitHub required jobs 全绿。

**验收：** 覆盖表无遗漏；每项显示值与 API/源事实一致；缺口有类型、原因和证据；状态/视口/下钻 E2E 通过；隔离 verify 19/19、浏览器 9/9；门禁与同 SHA CI 绿；常驻数据库未被测试写入。符合后更新 UX 工作包、路线图和 PROJECT_STATE，提交推送。

**遇到问题：** API 200 不代表页面正确；页面有卡片也不代表数据链通过。副作用不明时用静态调用链审查，不能 curl“试试看”。E2E 若因 Next `.next` 锁或临时配置冲突，使用工作包记录的临时 web 副本方案，不杀未知进程、不改真实工作区配置。常驻库批次问题只做只读核对，禁止擅自清理。

**完成后：** 进入第 3 项 C 级归因与修订。

#### 3. 公开财报 C 级归因、原件复核与抽取修订

**入口材料：** `docs/50_plans/work_items/PUBLIC--c-level-exit-protocol.md`、`docs/80_reviews/ai-cross-review/results/adjudication.md`、交叉评结果 `docs/80_reviews/ai-cross-review/results/gpt-6-astra-2026-09-25.md`、执行说明 `docs/80_reviews/ai-cross-review/README.md`。已确认 42 个真抽取异常并分类；另有 109 个字段口径疑点；JDL 200 格原不可核对的文本层问题已有英文版原件可读，SHA 见 adjudication §4。三类状态不得合并成一个“错误数”。

**操作步骤：**

1. 先对账最新抽取 YAML、订正表、提交和 L1 报告，确认 42 项裁决是否已进入版本化新 YAML；保留旧值，不覆盖原始财报和历史答案集。
2. 按 `adjudication.md` 模式一修空列借邻值：源列为破折号必须输出 null；为模式二修正 JDL 权益变动表页区间/表识别；为模式三补 BABA FY2023 prior。每种模式先添加失败测试，再最小修复。
3. 复核 109 项字段合同：确认 current/end/begin 语义、阿里现金流行名、流动/非流动限定、JDL 利润与综合收益归属。每项保留“原值/新值/口径理由/原页证据/复核者”；无法明确判定就标记未决，不静默归成数值错误。
4. 用可读 JDL FY2025 英文版对原 200 格逐格重核，英文版只作为同版式双语源文本，不替换/删除中文原件。复核时检查页码、行列和单位；pypdf 与答案包同族，注意不要把 pdfplumber 乱序误判为源错误。
5. 修订只产生新版本答案/抽取资产和 supersedes 链；更新差异分类和基准。执行 `python3 scripts/accuracy_benchmark.py --level L0` 和 `--level L1`，并运行受影响抽取/导入/解析测试。

**验收：** 42 项有逐项修订/保留理由；109 项有字段口径结论或明确未决；JDL 200 格全部核验或逐格保留不可读证据；原文值、抽取值、页码、单位和变化关系可追溯；L0/L1 结果与 SHA 归档。不能因 L0 通过宣称 L1 或 C 级通过。

**遇到问题：** 英文版数值列/页码若与中文疑似不一致，交叉检查原文版式和下载 SHA，暂停该格结论；PDF 文本层缺字时采用受审视觉/OCR证据并登记，不猜值。实现修订导致其他报告变化时跑全相关抽取集，不只跑单个样例。

**完成后：** 进入第 4 项 U04 parser 与冻结留出验证。

#### 4. U04 解析器适配与独立留出验证

**入口材料：** U04 工作包、`validation/financial_reports/oracle-register.md`、`validation/financial_reports/holdout-lottery-2026-09-25.md`、原始首跑 `validation/financial_reports/holdout_runs/2026-09-24/`、`docs/implementation/objective-analysis/holdout-results.md`。当前已冻结并录入 oracle 的留出是 `validation/financial_reports/oracle/xiaomi_2026h1.yaml` 与 `alibaba_fy2027q1.yaml`；原件在 `validation/financial_reports/original/` 对应目录。原 3 样本全部 199 行 not_comparable，是旧版式不可比，不是精度通过。

**操作步骤：**

1. 阅读当前 `cn_ashare_table` 适配器、页码配置、旧首跑产物、oracle-register 和抽签记录；确认候选原件 SHA 与 oracle 文件 SHA/来源匹配，先冻结原有首跑结果。
2. 注意 `scripts/holdout_u4_run.py` 当前 SAMPLES 默认仍是旧的 SF/Tencent/ZTO。**不可不加检查就把它当作新留出 runner。**先添加显式 sample 参数/配置及单测，能把旧样本跑作回归、将小米/阿里按冻结 oracle 跑作留出；输出目录用全新 run ID，绝不覆盖 `2026-09-24`。
3. 对 “合并及公司” 合并标题和年报页码提示范围写失败测试；解析器最小改造后跑旧 3 样本回归。新留出原件首跑前不看抽取输出调参，不修改 oracle 期望值。
4. 冻结新留出首次输出、source SHA、parser commit、命令与环境；逐行计 matched/mismatched/not_comparable，区别行名未匹配、页码范围、单位和真实数值错误。
5. 对差异逐项回原 PDF；独立性受损的样本立即转回归集并注明污染史，不可继续称为 holdout。

**验收：** 旧样本作为回归集有可比率/差异清单；小米和阿里按冻结名单、原件 SHA、未调参规则首跑；逐行差异和归因可复现；更新 oracle-register、holdout-results、U04 工作包和路线图。通过率门槛以 U04/C 级正式协议为准，不自设放宽线。

**遇到问题：** 如果解析器仍不能比较，保留 not_comparable 和最小复现，定位版式适配；不得将 not_comparable 算作 match。若新样本文件或 oracle 真缺失，先查 Git tracked 路径、manifest 和备份再认定缺失；无法恢复时执行外部材料调查/未验证结案，不伪造答案。

**完成后：** 进入第 5 项，重建 L0/L1 与 C 级 Go/No-Go 证据包。

#### 5. C 级质量基准与 Go/No-Go

**入口材料：** C 级出口工作包、更新后的抽取/答案集、U04 结果、发布与溯源测试证据。

**操作步骤：**

1. 检查 `config/statements/answer_set_l1.yaml` 是否由当前事实/来源版本确定性生成；需要重建时先保存旧版本和 supersedes 链，再运行 `python3 scripts/build_answer_set_l1.py`，不得静默覆盖历史答案集。
2. 运行 `python3 scripts/accuracy_benchmark.py --level L0` 与 `--level L1`；若需 DB，使用隔离 `flow_test` 或专属验收栈。记录完整输出、分母、strong/weak anchors、unlocated 和 mismatch 分组。
3. 按 C 级工作包逐项核验 L0、L1 ≥300 数值点/覆盖报告全集、公司级 holdout、页锚可复现、重述 supersedes 链、盲评无严重事实错误和拒答/降级行为。
4. 对每项未过门槛的证据开在当前第4项内继续修，不另开平行队列；按现有责任执行原件复核或代码修复，随后重跑相关与全量基准。
5. 形成机器可读结果和书面 Go/No-Go：只有所有硬门槛通过才写 Go；证据不足写 Hold/未通过并列精确缺口，不将覆盖 1794/1794 等同准确率。

**验收：** 同一最终 SHA 上所有规定门槛和 required CI 通过；答案集和来源可复算；Go/No-Go 引用每条证据 SHA/路径。随后更新状态并提交推送。

**遇到问题：** 发现旧文档与机器结果不同，以新鲜可复验机器输出为准并保留旧记录；若 DB 不可用先确认 Docker/服务并检查脚本是否会写常驻库，禁止为让测试通过而接常驻 `flow`。

**完成后：** 进入第 6 项 P3 数据扩张和来源接入。

#### 6. P3 真实数据、来源与行业扩张

**入口材料：** `docs/50_plans/work_items/PUBLIC--data-expansion-benchmarks.md`、公开来源政策、既有财报抓取/抽取/导入管线、`docs/80_reviews/ai-cross-review/results/adjudication.md`。

**操作步骤：**

1. 核实公开来源政策和下载授权，对每份报告记录公司、市场、报告期、报告类型、官方 URL、下载时间、SHA-256、页数和文本层可读性。
2. 逐批加入物流→电商→SaaS公开财报；任何批次先验 PDF 文本层，乱码时查官方英文版或可靠 OCR，并把原 PDF不可变保存。
3. 运行抽取、L0、每公司至少20点 L1 抽核、勾稽检查、页锚和 source/supersedes 关系；导入或发布仅在隔离栈完成。
4. 行业基准逐条记录来源、时期、样本和计算方法；缺少可靠来源就标 unavailable，不编行业数字。
5. 运行性能脚本并形成 P95 报告及复跑脚本；阈值以既有决策/批准规格为准，不擅自固化建议阈值。

**验收：** 每个批次原件和派生产物 SHA 齐全，L0 全绿、L1 样本及勾稽有记录、报告身份/重述链不冲突，性能结果可重放；同 SHA CI 绿。

**遇到问题：** 下载失败查官方页面/API并保存 HTTP/时间证据；替代文本层必须能证明与原件同版本。行业基准或真实原件缺失时完成来源检索报告和“未纳入”结案，不能伪造，也不停止本队列该项其他可做的来源/工具工作。

**完成后：** 进入第 7 项第二代静态知识 refresh。

#### 7. 第二代静态知识 release 与战略重基线

**入口材料：** `docs/50_plans/work_items/KNOWLEDGE--refresh-v2.md`、规格 `docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md`、实施细节 `docs/superpowers/plans/2026-09-18-static-knowledge-refresh-and-strategic-rebaseline-implementation-plan.md`（该实施计划已 archived，不维护状态；只取 K0–K6 方法/命令）、Davybase 与 ObsidianWiki 仓库。正式 release 仍是 `flow-knowledge-2026-09-12.1`。

**操作步骤：**

1. **K0**：同步 Davybase/ObsidianWiki 最新 canonical remotes；记录各仓 HEAD、tree、dirty、批次/分母与依赖版本；验收旧图片批次 manifest，逐样抽查，确认输入/成功/过滤/失败互斥对账。不得覆盖原文或原批次证据。
2. **K1**：对非微信核心知识目录（企业管理、财务会计、跨境物流等）先 allowlist dry-run，检查 coverage 与敏感边界；抽查路径解析，运行 apply/有限 retry；逐项终态必须闭合。只用生成的 pathspec 暂存对应 Obsidian 文件，不 `git add -A`。
3. **K2**：严格执行 Obsidian Git 冻结流程：14:30锁定、15:00候选、15:30复验；要求两个时间点 commit/tree 相同、工作区 clean、canonical remote 可取。只有 accepted manifest 才可作为后续输入；失败则写 rejected 记录，下一可用日重试，禁止伪造时间或自动提交不明修改。
4. **K3**：只用 K2 accepted manifest 重建来源 registry/baseline/diff；按稳定 ID 做新增/修改/删除/改名差异；敏感/排除数据仅留聚合统计。相同输入重建两次结果 SHA 应一致。
5. **K4**：按冻结 scope 做全量路由和高价值精读，明确 coverage 分母与互斥终态；对 HIGH 回读，记录失败集中与误分类复核；生成影响 FLOW 的新素材、领域手册与采用映射，不把 L2 发布知识直接当产品既定规则。
6. **K5**：构建 candidate、来源/coverage/reader 问题包，独立读者复核；满足 sealed lock、哈希和 reader 门槛后 seal。candidate 未 sealed 不开始正式战略影响结论；始终保持 `CURRENT_RELEASE` 不变。
7. **战略裁决/S0–S1**：对目标、角色、报告工作流、模块可见性、规则可见性、真实数据验证等逐条形成证据、影响、替代方案和风险；正式决策由用户作出。无需每步问用户；仅这一规格明确保留的战略裁决点不可由 Agent 冒签。若接手时没有相应正式裁决，不得激活 release 或把候选写成已采用；先完成所有不依赖裁决的审计/影响材料，列明唯一待裁决问题和选项，状态保留“sealed candidate、未激活”。由于该裁决是用户主体不可代理，不能伪造“外部材料不可得”来绕过；须把当前项原验收未满足、候选未激活及可恢复的下一步写入路线图与交接，再停在该项，不得擅自推进后续队列或替用户裁决。
8. **K6/V**：按规格在一个原子变更集合里激活 release、更新产品当前文档和唯一路线图；先在干净独立 checkout 对精确 SHA 复验，过门禁后推送、等 CI。失败用新的普通 revert/recovery commit 恢复整套一致状态，不改写历史、不只回滚指针。

**验收：** 三仓库身份/hash/coverage/失败列表可重放；15:00 snapshot accepted；source baseline 四维差异对账；coverage/reader gate 全 PASS；战略决策记录已存在；release lock/manifest hash 一致；activation 同 SHA 独立复验与 CI 通过。每个代码/知识原子任务在所属仓库单独提交推送，然后才进入下一 K 步。

**遇到问题：** 当前命令或脚本不存在时，先检索实际 CLI 和测试，再按 archived plan 的规格补工具与红绿测试，不照抄未实现命令。锁冲突不抢锁；Obsidian 有未归属改动不覆盖；敏感路径不得传到 FLOW 或外部模型；15:00 不稳定时明确 rejected 并顺延，不降低冻结标准。

**完成后：** 进入第 8 项 `rnd_exp` 来源核验。

#### 8. `rnd_exp` 官方依据核验（外部材料受限项，主动恢复后结案）

**入口：** 路线图记录的《应用指南汇编 2024》核验和暂记 `4301`。先 `rg -n "rnd_exp|应用指南汇编" .` 搜仓库，再查知识库来源登记、公开官方发布渠道和可验证归档；记录查询关键词、站点、访问日期、版本、URL 和 SHA。

**步骤与验收：** 找到原件时冻结原件和 SHA，逐项核对原文定义、期间、符号、公式与 `rnd_exp` 来源，更新指标口径登记与测试；找不到时完成有来源的检索过程、可替代权威来源比较、为什么不足以等同原文、哪些字段保持 unverified、影响到的指标/报告和重启条件。后者只能结案为“官方依据未核实”，不能写成核验通过。

**遇到问题/下一步：** 链接失效先查官方站点检索/网页存档/公告附件；不同版本不一致则逐版登记不自行挑有利值。完成“已核实”或“原件不可得的证据化结案”后才推进第 9 项。

#### 9. U09/O05 内部试点

**入口材料：** `docs/50_plans/work_items/U09-O05--authorized-internal-pilot.md`、`docs/20_product/` 的主数据/经营分析规则、战略设计与已批准的内部数据治理规格。用户已授权本项目实施，不再等待泛化的“数据授权批准”；但只允许使用当前确实可合法访问的数据，不能虚构真实企业事实。

**操作步骤：** 先按工作包合同核验企业/组织/科目/客户/产品/期间主数据身份、输入版本、来源、内部事件簿、收入/成本/利润守恒；再走月度批次导入、规则/指标匹配、分析计算、证据组织、AI 结论与经分专员审核发布的完整技术流程。若无真实企业输入，使用大麦 synthetic 仅做流程/接口回归，并把真实试点证据状态单独标未验证。

**验收：** 一报一会闭环、主数据与版本追溯、多维盈利守恒、六主题经营分析与异常证据可追溯；角色边界符合已定原则；synthetic/真实结果分开标记，不把年度公开数据摊月，不伪造 L2/L3。

**遇到问题/下一步：** 缺真实输入就完成脱敏 schema、字段映射、导入/拒绝和技术 E2E；形成精确的真实数据缺口与可接入格式说明。完成技术闭环及诚实的证据状态后进入第 10 项，不以“等批准”停工。

#### 10. U10 V1.1 证据决策

**入口材料：** `docs/50_plans/work_items/U10--v1-1-evidence-decision.md` 及其底稿 `docs/90_archive/plans/2026-09-07-v11-evidence-decision-pack.md`。U08 已完成；使用现有 U04、C 级、U09/O05、知识/大麦证据，不能把仍缺的证据补写成完成。

**操作步骤：** 将每项 V1.1 候选能力列为 go/hold/drop；每项记录主张、证据及 SHA、来源、适用范围、风险、反证、缺失证据、替代验证。对没有证据的项按规则 hold；如果已有证据足以裁决其他项，不因少数 hold 项停止整包裁决。形成正式决策记录并关联唯一路线图。

**验收：** 决策包覆盖全部候选；每项 go 有充分证据，hold 有可执行解锁条件，drop 有理由；决策不超出现有用户战略边界；文档门禁和同 SHA CI 通过。

**遇到问题/下一步：** 指标矛盾则回到原始 run/报告 SHA 核实；只对受影响候选改状态，不推断整项全局通过。提交推送后推进第 11 项。

#### 11. 内部月度工作台与四级真实周期验收

**入口材料：** 路线图状态表中的内部月度工作台/四级验证、战略设计 §14.2、U09/O05 工作包、已 sealed/正式采用的知识与指标规则。该项是最终真实经营验证，不由大麦 synthetic 或公开年报代替。

**操作步骤：** 在既有企业工作台中冻结真实月度输入和来源版本；逐月由 BP 提供数据、系统生成指标/归因/证据/分析结论、经分专员审核发布。每周期保留系统输出、同输入人工基准、盲评记录和实际工时；连续完成三个真实月度周期，不在周期中途改基准或删除失败记录。

**验收：** 三个周期均有完整源数据/版本和报告；人工对照同输入；逐周期盲评满足规格；工时降低达到 20% 门槛；无严重事实错误；能复算报告结论。最终结论只在真实数据证据齐备后给出。

**遇到问题与最终结案：** 若本机/企业没有真实月度数据，先完成 synthetic 技术验证、环境复现和数据接入说明，再形成“真实四级验证未完成”的正式结案，标出所缺的三个月数据及可重启条件；绝不宣称达到真实企业验收。因为它是队列末项，报告为战略验收尚未完成，而不是无限等待或虚假关单。

### 每个队列项的固定关单与交接协议

1. 开始前：`git pull --ff-only`；确认 `main`、clean worktree、HEAD 与 origin 一致；核对当前只允许队首任务执行。阅读本卡对应工作包和规格。
2. 执行中：先记录当前任务的细分步骤数及逐步状态；实现按 TDD，数据任务留原件 SHA 和命令；小步完成但不同时开后续任务。
3. 验收时：按上方对应门槛逐条跑，保存完整命令、退出码、摘要、环境和 SHA。测试失败不等用户帮忙诊断，先复现并修复；如果遇外部缺项，执行该卡替代闭环协议。
4. 文档与提交：更新对应工作包、`CURRENT_ROADMAP.md`、`PROJECT_STATE.md` 和本 HANDOFF 中必要的当前快照；仅暂存本项文件；`git diff --check`、`python3 scripts/check_docs.py --phase m1`、相关 links/contract/tests 通过后 conventional commit 并立即 `git push origin main`。推送失败按 AGENTS 立即报告确切原因和修复方法。
5. 进入下一项：只有当前卡达到“原验收通过”或“外部受限但替代结案已完成、且明确记录原验收未满足”之一，才能更新计数并启动下一项。不能因为一项复杂或耗时而跳过，也不能把一个 item 拆成并行 Agent。
6. 续接播报：向用户提供 11 项完整队列、项数/计数、当前唯一 item 的子步骤进度、已完成证据、限制与已尝试恢复法，以及唯一的下一动作；没有运行中的进程时必须说“未启动/已暂停”，不得写 active 冒充进行中。

**下一位 Agent 接手后的唯一下一步：** 拉取 `main` 并核对分支/HEAD/CI；检查原终端能否回收 `tests/fixtures/test_damai_loader.py` 的退出码，否则在审阅工作区差异后重跑该测试。接着逐一审阅保护当前未提交的 loader 修改、组织模型、企业服务、0031 迁移和两份测试，与 `fc6e63a7` 批准的三表方案比对。随后按单项顺序补齐合同/负向测试与隔离迁移验证。schema 已获批准，但只可在隔离栈执行迁移和初始化；不得先做 UX、C 级、知识刷新或其他队列项。

> **当前状态覆盖（2026-09-26 深夜·ZCode 夜班会话收尾）**：本交接基于 `main@e78f0616`（本会话最后提交为 `b161fff`，其后并发会话叠加 UI 可链接性审计）。本会话四项交付已全部入主线：**①归因裁决 `4111f6a`**（42 异常全判真实抽取错误+证据忠实性 100%）；**②新留出双样本 `926af82`**（小米 2026H1 + 阿里 FY2027Q1 冻结+oracle 录入完成——注意：v3.6 所记“候选 PDF 未冻结”已过时）；**③测试库隔离根因修复 `b60c51b`**（conftest 默认切 `flow_test`，实证常驻库零污染——v3.6 所记“最高安全前置”已完成）；**④JDL 英文版冻结 `b161fff`**（210 页文本层可读，200 格重核输入条件已具备）。C 级出口仍未通过；抽取器修订（实现方职责）与新留出首跑是剩余关键路径。

## 0.3 本轮交接（2026-09-26 ZCode 夜班会话）

### 当前任务快照

会话从「合并 GPT/Kimi 反馈 + 交叉评归因」接手，按用户授权（连续执行、推荐方式自决、不停顿）完成 P0–P3 四项关键路径交付。会话角色定位：**非实现方裁决/核验方**（GLM，未参与抽取器开发；oracle 登记册 §1a 授权录入者）。

### 已完成（本会话四提交，全部已推 main）

| 提交 | 交付 | 要点 |
|---|---|---|
| `4111f6a` | **P1 归因裁决** | 42 异常逐条对照原始 PDF：**全部真实抽取错误**、评审证据 100% 忠实。三模式：菜鸟 19 格破折号列借邻值（列对齐缺陷）、JDL 22 格权益变动表误入 BS（页区间缺陷）、BABA 1 格漏抽。109 存疑=字段合同问题非数值错误。产出 `docs/80_reviews/ai-cross-review/results/adjudication.md`（含实现方修订工单第五节） |
| `926af82` | **P3 新留出冻结+oracle** | 小米 2026H1（新公司；中英双版 SHA；中文版文本层乱码→oracle 以英文版录入，7 key items+19 行）+ 阿里 FY2027Q1（新期间；5 key items 含 Non-GAAP 20,715 百万）。manifest holdouts 双条目+oracle-register §3 双行登记 |
| `b60c51b` | **P0 测试库隔离根因修复** | conftest 本地默认从常驻 `flow` 切到自动创建的 `flow_test`；CI（GITHUB_ACTIONS）自动豁免零 CI 改动；`FLOW_TEST_ALLOW_PERSISTENT_DB=1` 显式豁免通道。5 契约测试+实证：10 个 DB 测试跑隔离库，常驻库大麦数据前后均 2 报告**零污染** |
| `b161fff` | **P2 JDL EN 版冻结** | 京东物流 FY2025 英文年报（披露易 2026/0424/2026042401322，210 页，SHA `32a99c3a`）冻结至 `original/jdl_fy2025_readable/`；第 110 页验证可读且与中文乱码版逐字一致——200 格重核解锁 |

（同会话更早还有：oracle zto `4acc1c3` + tencent `e8f2624` 录入；EXECUTION_TODO 落盘——后者已被 2A 裁决归档为参考。）

### 卡住 / 未完成（按阻塞优先级）

1. **抽取器修订（实现方 GPT 职责）**：adjudication §5 是完整工单——列对齐算法修空列借值、JDL 页区间修正、BABA prior 补抽、109 存疑字段合同裁决。修订须新版本进入（保留旧值+证据）→ 重跑 L1 基准。**首跑前任何人不得用新留出样本调参**。
2. **JDL 200 格逐格重核**：EN 版输入已冻结（`b161fff`），需专注会话执行逐格对照（EN 版对照法先例：小米 oracle）。
3. **U4 首跑（新留出盲测）**：小米/阿里 FY27Q1 的 oracle 已备，等抽取器修订完成后执行；旧三留出（tencent_fy2025/sf_2026h1/zto_2026q1）按污染史规则转回归集。
4. **C 级 Go/No-Go**：依赖 1+2+3 全绿；`1794/1794` 只是台账覆盖口径≠出口通过。
5. 大麦 UX 收口、ZTO 样本接入、K0–K6 静态知识：按 CURRENT_ROADMAP 排队（并发会话在推进 UI 线，`e78f0616`）。
6. 遗留分支 `codex/frontend-consistency-remediation`：两套前端 UI 路线分歧（组件库 vs css），在途修改已保全于分支 `2b53bbe`，待用户选型。

### 下一步（推荐顺序）

1. 查 `b161fff`/`e78f0616` 对应 CI 最终状态（提交级核对，见踩坑#2）；
2. JDL 200 格逐格重核（EN 版对照；独立会话或本会话续作均可）；
3. 催办/等待实现方按 adjudication §5 修订抽取器 → L1 重跑；
4. U4 首跑（新留出盲测）→ C 级 Go/No-Go 裁决；
5. 其后按 CURRENT_ROADMAP 顺序（UX 收口 → K0–K6 → 部署验收）。

### 本会话踩坑实录（新增）

1. **多 worktree + shell cwd 漂移 = git 误操作高发区**：本会话曾误把 `reset --soft` 打在主工作区的 audit 分支上（当时 cwd 已被重置），靠 `reset --hard <原HEAD>` 恢复；另有一次 `commit --amend` 误改写已推送提交，需软重置回远端基线重新提交（禁强推）。**对策：每条 git 命令前自校验 `git branch --show-current`；worktree 操作必须显式 cd 且命令内验证。**
2. **CI 状态是提交级事实**：报“CI 绿”必须核对与提交相同 SHA 的 run；前一提交绿不代表后一提交绿。
3. **中文 PDF 文本层乱码规律**（EN 版对照法先例已两次验证）：阿里系/腾讯/顺丰中文版正常；**京东系（年报+业绩公告）与小米中文版全部乱码（嵌入字体映射损坏），其英文版文本层完全可读且与中文版同版式双语排版、数值逐字一致**。遇到新样本先验文本层，乱码即抓 EN 版。
4. **psycopg 不认 SQLAlchemy URL**：`postgresql+psycopg://` 会被当非法连接串，直连 psycopg 须剥 `+psycopg` 后缀。
5. **pypdf vs pdfplumber 文本层差异**：同一页 pdfplumber 可能输出镜像乱序而 pypdf 正常（菜鸟 473 页实例）——核对证据时用与生成器同族的提取器（pypdf）。
6. **alembic revision ID ≤32 字符**：超长会在版本表写入时报 `StringDataRightTruncation` 且迁移半途回滚。
7. **worktree 无 .venv**：用主工作区 `services/api/.venv` + `PYTHONPATH=src` 运行 worktree 测试。
8. **测试连常驻库事故根因已修**（`b60c51b`）：今后本地跑测试无需再担心清掉开发库；`flow_test` 库按需自动创建、跨会话复用。
9. **港交所披露易可编程下载三步**：`prefix.do`（代码→stockId）→ `titleSearchServlet.do`（搜公告，注意 result 是需二次 json.loads 的字符串）→ 直链下载；中文版 `_c.pdf`、英文版无后缀或 `_e`。

### 历史踩坑（保留）

- 交叉评的“42异常、109存疑、200不可读”是三种不同处置状态，不能合并成同一个“错误数”或宣称 C 级通过。
- 本地未跟踪财报属于工作区材料，不要 `git add -A` 盲扫；候选样本冻结前不得当成正式 holdout。

## 0. 执行摘要

### 0.1 当前可信结论

- **历史基线：`main@a461b54`**（2026-09-19 晨，全 job CI 绿）；当前集成主线以本页顶部覆盖状态为准。
- **S01 / U8 关闭不变**；阶段 3 基础（T09–T12）与 C 级出口执行批次交付不变（台账 §8/§9）。
- **指标库 v1.2 行业参考包已交付**（借鉴 #21：16 行业 + 流动资产率 + 基准增强，`5442d9c`）；**O-01/O-02（AI 问数 v2 地基）已落地**（语义上下文端点 + 提议→复算管线，`3a0ee20`）。
- **前端一致性整改计划 Task 0–9 全部关闭**（P3–P5 批次：metric-library/investigations 深度迁移、状态门禁 frontend-states.spec、60 图状态矩阵归档；门禁矩阵 = 一致性 10 路由 + 溢出 11×3 视口 + 状态 5×3 + 导航/边界 = 69 项，全跑生产构建）。
- **后端既有 flake 修复并 CI 实证**：objective freeze 幂等的行序漂移（`0af6a8a`，publishing-golden 绿）。
- **数据来源政策已由用户明确（2026-09-19）**：无私有数据来源，研发期一律网络公开来源数据——A4「等待外部财报材料」的前提作废，数据扩张改为继续走公开财报抓取管线（见 §2.2/§2.3）。
- 多 Agent 并行已终止，单一 Agent、逐 Gate、串行执行不变；产品战略方向不变（经分专员工作台，公开财报独立先行）。
- **下一里程碑不变 = C 级出口 Go/No-Go 裁决**；前置人工项不变（见 §2.2）。
- **大麦物流两年 synthetic 演示数据全链已交付并集成 main**：实施细节和原始分支证据见 §2.5；当前主线集成验收以顶部 `e22d193` 与 run `36137591750` 为准。

### 0.2 当前最重要的偏差与缺口

| 类型 | 当前判断 | 处理方式 |
|---|---|---|
| 10 条抽取错误候选 | BABA NCI 8 条 + JDL 现金流 2 行，值在源 PDF 文本层不存在（压力测试实锤） | 人工翻页查源（压力测试报告 §2 清单）→ 修抽取 YAML 新版本 → 重跑基准 |
| C 级出口 PASS | 独立交叉评已完成但发现42个确认异常、109个存疑，JDL尚有200格不可完整核验；抽签有候选但未形成冻结oracle | 原PDF归因/订正 → 可读源文本 → 新留出冻结/独立录入 → 盲测与基准复跑 → Go/No-Go |
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

- **完成证据**：verify 19/19（`make damai-demo-verify`）；八页面真实 E2E 9/9（`make test-damai-demo-e2e`，隔离栈 + Playwright，38s）；数据合同 8/8（含二次 seed 计数零增长）；U8 非破坏升级验证全链 PASS（dump SHA 核对 + 恢复 11 财报 + HTTPS 三方对账，证据 `work/s01-verification`）；M6 文档门禁绿（278 docs, 0 errors）。原 worktree 升级路径到 0029 是历史测试记录；当前 main/开发库迁移头均为 0030。
- **数据实测**：24 个月（FY2025–FY2026）、1920 经营实际 / 10752 预算 / 4800 AR / 672 财务实际、4 客群 / 40 客户 / 8 产品 / 6 区域 / 5 组织；指标覆盖 FY2025 22/40、FY2026 25/40（来源 `fixtures/damai/manifest.json` 与覆盖包）。
- **红灯抓出并修复的真实缺陷**：reports-center 两个发布 fetch 缺 `Idempotency-Key`（§7.1 合同）+ Next 代理丢弃该头——已修并补单测。
- **一键恢复**：`make damai-demo-up`（构建发行包 → 迁移 → seed → verify）；分步 `damai-demo-build/seed/verify`。
- **已知限制**：dashboard 总量域 OCF actual 不存在是合同真相（state=degraded 为预期）；合成数据不解除公开 C 级与真实企业门禁；常驻开发库装载已另行完成并记录于 CURRENT_ROADMAP G2；G2 过程中出现的共享库测试误连与补种事故详见 To-do 历史记录，避免无隔离地运行会清理数据的测试。
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

## 8. 下一位 Agent 的第一条动作（历史指引，当前以 CURRENT_ROADMAP 为准）

旧版建议以 `a461b54` 为基线；当前接续必须按 [CURRENT_ROADMAP](docs/50_plans/CURRENT_ROADMAP.md) 对远端状态、CI 与执行队列重新核对，不沿用该旧顺序。

当前对外状态统一表述：**U8 closed；S01 completed；前端一致性 Task 0–9 关闭；大麦两年 synthetic 实施已集成 main（`e22d193`，CI run `36137591750` 17/17）且G2常驻库装载通过；U4需解析器适配与真正独立新留出；C级交叉评已发现42个确认异常、109个存疑和200格不可完整核验，仍须原件归因/订正、留出冻结与独立验证；知识 release、P3、UX收口及后续内部真实周期验证按 CURRENT_ROADMAP 顺序处理。**
