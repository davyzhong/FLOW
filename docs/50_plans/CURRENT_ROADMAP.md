---
doc_id: FLOW-PLAN-CURRENT
title: 当前路线图（唯一）
doc_type: plan
status: active
version: 14.1
created_at: 2026-09-12
updated_at: 2026-10-26
owner: FLOW
depends_on: [FLOW-SPEC-V1-DESIGN-001]
acceptance_refs: [roadmap-unique-invariant]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: planning
supersedes: [FLOW-PLAN-UNIFIED-000, FLOW-PLAN-OPS-000]
superseded_by: null
---

# 当前路线图（唯一主线）

> **2026-10-26 最新状态：** D055 单机原型 7a.1–7a.8 已合入 main；视觉语言包及全项目页面、图表、报告/离线输出和 README 视觉统一已完成。路线图仍为 16 项：完成 10、实际执行中 1（K 轨 K3）、排队 3、暂停 1、外部条件受限 1。视觉覆盖验收：隔离 synthetic manifest `6f3ef9176aaa02009c36080621d40ff6212ab1189c6e2c0695f5ea5f1b688fed` 下验证器 19/19、可见性矩阵 164/164（154 HTTP 200、10 预期拒绝、0 失败）、Playwright 17/17；20 路由×3 视口 60/60 与 Axe 桌面 20 路由零违规仍对应应用 SHA `01e8e25dd426ed43ad6a2cad76544bbbe623eb99`。最新 E2E 断言修复已提交于 `d01daa11`，独立复核无 P1/P2，`git diff --check` 通过。原生浏览器 200% 缩放因 Mac 锁屏且当前工具不能操作 Edge 工具栏，未直接验收；390/360 CSS px 证据不替代。按外部条件受限替代结案，待设备解锁且可控工具可用时补验。当前分支 `codex/flow-visual-language` / PR #5；工作包结案文档随后提交并以准确 SHA 查询 GitHub CI。视觉包证据见[覆盖验收](../60_delivery/verification/2026-10-24--flow-visual-language-coverage-v1.md)。下一唯一事项 K 轨当前子步为 K3 语义审阅前置复核：当前 accepted snapshot `obsidianwiki-20261026T005516+0800-d601b4d5`（manifest SHA `593715c832a538d9ba83df4e077b8dd9bace24f40d3c0d5262fc3779b20f0e77`）候选/复验一致、内容 SHA `c84efd671e2b90e4f69152c3dd04a570d9c378d08fb7a3cb97b86e322f123df0`、可写句柄 0。新 snapshot 与之前 K3 基线内容指纹一致；registry/baseline/delta 已绑定最新 snapshot 并重复构建一致。当前按序进行全量逐条主题路由及 coverage 闭合；全量路由已完成至第091批，coverage 为 routed 415、filtered 176、pending_review 9,082；下一动作是第092批。当前有五个 locator-only / pending-review 例外（新增 `SRC-LOCAL-v1-0de553da4d8d857b90d3`；其他包括 `SRC-LOCAL-v1-00625bae4e08042539d1`、`SRC-LOCAL-v1-0428a240b0361157ffa1`、`SRC-LOCAL-v1-057cabfb9baca9f47c44` 和 `SRC-LOCAL-v1-0bd79ce2c2d600301852`），均未使用范围外内容或链接标题推断。HIGH 全读及 MED/LOW 双审已完成。旧 10-19 baseline/diff 保留为历史结果。ObsidianWiki 和 `CURRENT_RELEASE` 保持不变。

> 当前完结目标依据 D055：交付本机单用户可启动、可加载/重置演示业务、可看丰富 CFO 图表、可下钻追溯、可分析和导出报告、可备份恢复、可离线浏览的验证原型。公开 C 级、知识刷新、真实企业三周期仍未完成，保留在长期队列，不作为本原型无限延期的理由。**下方 2026-10-21 及以前的状态段落均为历史，当前只按本段及唯一执行队列。**

> **2026-10-20 main 基线（历史快照）**：当时 main HEAD `5ed61af91ea4c1c2a2078fd654accf671ba805ba` 对应 GitHub Actions run `39119888132`，18/18 jobs success；唯一队列为 14 项（完成 7、执行中 0、队首待启动 1、排队 4、暂停 1、外部条件受限 1），队首为 D055 单机原型架构简化与全视图视觉升级。此快照早于本分支后续进展，不代表当前状态。

> **2026-10-21 历史状态：单机启动/本机验收、门禁拆分已完成；7a 仍在收敛全视图视觉差距和文档治理。** 费用页 KPI 修复 SHA `87e1829d32d6281fe1dad7ee978f39e0c1b4e5f2` 的准确 SHA CI run `39451521454` 因后续提交已取消；期间费用堆叠对比提交 SHA `65d7dc61d18e0ebe2f2bc582c3f99e4bbe3e4d5d` 的 CI run `39453419044` 因后续状态提交取消；汇总 job 标记失败的原因是分片被取消，非测试断言失败。状态提交 SHA `a71cb28eedc6bca8019e7552fe7b2348f28f1239` 对应 run `39453752316` 已 28/28 success；最新文档提交 SHA `21b650a108e7d906338454d661b7cfe178e13487` 对应 run `39457446117` 已 28/28 success。上一文档 SHA `4073d511` / run `39447663998` 为 28/28 success。此前代码 SHA `2f1b549...` / run `39447424948` 被后续提交取消，不据此判断失败。本轮修复 390px 费用页五项 KPI 栅格：原规则被特异度更高的三列选择器覆盖，现改为两列并新增隔离响应 fixture E2E。进一步将驾驶舱期间费用图改为 API 已发布的两年四项披露费用堆叠对比，并同步双期间原值表，注明不含营业成本、不推算费用率。前端 199/199、typecheck、生产 build 通过；lint 零错误、3 条既有警告；文档 M1/M2/M6 通过。六个主题模块在 390px 实测 ready、有图表且无横向溢出。README、PROJECT_STATE 与运行架构文档已校正；疑似清理项只做引用审计，不删除文件。截图位于本机 `/tmp/flow-cockpit-visual-20261020/`，没有恢复截图自动化工作流。架构继续采用 SQLite、本地文件目录、同步处理和单一启动入口，本轮未增加依赖/服务或改数据库。原 284 项/66 文件集成测试分片零遗漏、零重复，准确 SHA `368a01902124351401d73dc9329800d7f00f3953` / run `39349190031` 为 28/28 success。仍需完成文档审查、最终复核和准确 SHA CI 后才可结案。详情见[阶段 9 执行卡](work_items/FLOW--single-machine-visual-prototype.md#9-概念图视觉差距门禁负载与文档治理)。

> **2026-10-18 用户确认原型方向并完成队首重规划**：当前交付定位调整为单机单用户验证原型；用户选择 SQLite 单文件 + 本地文件目录、移除 Redis/Celery/MinIO，并确认 A 主风格 + C 报告叙事。旧驾驶舱全视图工作包归档，其九页/25 图与桌面/手机实测作为回归基线。旧 CI 实际结果为：`39042517573`、`39041228479` cancelled；`39040652008`、`39038535194` failure；不得描述为 CI 全绿。新的唯一队首为单机原型架构简化与全视图视觉升级，正式设计见[规格](../superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)与[D055](../10_governance/decisions/D055--单机单用户验证原型.md)。README 视觉基准说明提交 `d51af7ad` 的准确 SHA 主 CI run `39087270646` 曾因 data-contract 与 intake-e2e 到达 40/45 分钟 job 上限而 cancelled；同一代码的后续文档状态提交 `a331f03075c95f3b371b5a0ebd0fd91cac9dfeae` 对应 run `39090417203` 全部 job success，取消未复现。未改 CI 超时或缩减覆盖。第 1 阶段现状/影响审计已完成，清单与风险见[审计报告](../60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)。README 视觉素材编排已完成，只用仓库已有概念板与截图；截图素材采集/自动生成工作流继续暂停，未触发。D055 第 2 阶段 SQLite/本地内容存储已完成：隔离全链和兼容性验证通过；残留 PostgreSQL 专用 `.astext` 测试查询已改为跨库 `.as_string()`。准确代码 SHA `b0e1eb787592ff84bc4c19873a1e61cad1f9f3e6` 的 GitHub Actions run `39099573268` 为 18/18 jobs success，第 2 阶段正式关闭。第 3 阶段现已实现并本地验收：同步处理、本地内容寻址文件存储、单一启动入口与 SQLite 默认数据目录完成；隔离 Damai 账套重置回归 2/2、SQLite schema/jobs/object-store 16/16、设置/重置 PostgreSQL 兼容回归 2/2、Ruff/mypy、文档 M1 均通过。`make flow-bootstrap` 生产依赖裁剪增加 `CI=true` 以支持无 TTY 环境，完整引导成功；临时目录初始化成功，Web 与 API health 均 HTTP 200。详细证据见[第 3 阶段验收记录](../60_delivery/verification/2026-10-18--single-machine-runtime-convergence-v1.md)。本阶段仍待本提交准确 SHA 的 GitHub CI；通过后按序进入第 4 阶段全视图 A+C 视觉与数据补全。整个工作包完成后再恢复知识刷新 K2。
> **2026-10-19 工作包 7a 已关闭，K2 转为唯一队首**：4.6 指标期间、方向、单位与来源链接已修复，独立审查无 P1/P2，详见[指标展示验收](../60_delivery/verification/2026-10-18--cfo-metric-display-and-traceability-v1.md)。4.7 隔离真实数据验收覆盖 9 个 CFO/数据页面及 165 项浏览器回归，详见[浏览器验收](../60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)。代码 SHA `65a087063ad67702172430702590083f8991a884` 的 run `39139310634` 18/18 success；最终文档 SHA `a1fe50ef4e71298767b4fe8e22ab47d780f28552` 的 run `39140563811` 18/18 success。中间文档 SHA `8bf7535c` 曾有 M6 metadata failure 与 data-contract cancelled，已在 `a1fe50ef` 修复并全绿。工作包 7a 正式关闭，验收见[4.6](../60_delivery/verification/2026-10-18--cfo-metric-display-and-traceability-v1.md)和[4.7](../60_delivery/verification/2026-10-18--cfo-browser-acceptance-v1.md)；当时 K2 为唯一队首，后续验收以本页最新状态为准。
> **2026-10-18 第 4 阶段 4.5 完成，4.6–4.7 本地验收完成，最终门禁待结案**：修复大麦发行数据包与当前源 fixture 的血缘及内容漂移：`verify` 强制校验源 `manifest.json` SHA，并逐文件比较 canonical/statements/operations/forecast/workbooks；重建后 31 个文件通过验证，1,920 条经营记录与源文件一致，`order_count`/`shipment_count` 无非整数值；重复构建全目录摘要稳定。相关 14 项发行包/演示清单测试、Ruff 和 M1 通过，详细证据见[4.5 验收](../60_delivery/verification/2026-10-18--cfo-enterprise-package-lineage-and-integer-counts-v1.md)。没有连接数据库或改变公开事实，4.6–4.7 已完成本地验收，当前仅剩准确 SHA CI 和最终集成门禁。
> **2026-10-18 第 4 阶段子步 4.1–4.3 已结案，当前执行 4.4**：准确 SHA `d8f2ae8d617914fcd05cfd21d8484154b1411a65` 的 GitHub Actions run `39128676851` 中，除 `data-contract` 外所有 jobs 成功；该 job 初跑及一次重跑均在约 40 分钟上限被取消，没有测试失败结论。未继续重跑、未修改 CI 或降低覆盖。隔离 Compose 项目与独立库执行完整 `scripts/test_data_contract.sh` 成功：133 项夹具/契约测试、3 项数据库往返测试、Ruff、213 源文件 mypy 与摘要检查全通过。M1/M6、文档链接和 diff 检查通过。证据见[验收记录](../60_delivery/verification/2026-10-18--cfo-reference-matrix-ci-and-isolated-validation-v1.md)与[覆盖矩阵](../60_delivery/verification/2026-10-18--cfo-reference-module-data-coverage-v1.md)。据完整隔离替代验收关闭 4.1，保留远端 40 分钟取消这一限制；唯一子步推进到 4.4：按已批准组件/交互方案开始实现视图。
> **2026-10-18 第 3 阶段关闭，第 4 阶段启动**：第 3 阶段代码 SHA `a2ce20644217ece4bae0635794b41f2256cedba7` 首轮 CI 暴露初始化包 manifest 哈希未同步；修复 SQL 清单后，最终状态提交 SHA `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 的 CI run `39125304357` 为 18/18 jobs success，第 3 阶段正式关闭。实现、隔离验收和首轮问题处置记录见[阶段 3 验收记录](../60_delivery/verification/2026-10-18--single-machine-runtime-convergence-v1.md)。第 4 阶段按已批准工作包开始，唯一当前子步为 4.1：将参考文章的 10 个模块映射到现有路由/API/指标字典/真实数据，核实页面和数据覆盖、粒度、来源及缺口；先产出可审阅的覆盖矩阵，再决定逐视图增强顺序，不先加页面或图表。截图采集与自动化工作流仍暂停。工作包完成后再恢复知识刷新 K2。
>
> **2026-10-18 用户确认原型方向并完成队首重规划**：当前交付定位调整为单机单用户验证原型；用户选择 SQLite 单文件 + 本地文件目录、移除 Redis/Celery/MinIO，并确认 A 主风格 + C 报告叙事。旧驾驶舱全视图工作包归档，其九页/25 图与桌面/手机实测作为回归基线。旧 CI 实际结果为：`39042517573`、`39041228479` cancelled；`39040652008`、`39038535194` failure；不得描述为 CI 全绿。新的唯一队首为单机原型架构简化与全视图视觉升级，正式设计见[规格](../superpowers/specs/2026-10-18-single-machine-visual-prototype-design.md)与[D055](../10_governance/decisions/D055--单机单用户验证原型.md)。README 视觉基准说明提交 `d51af7ad` 的准确 SHA 主 CI run `39087270646` 曾因 data-contract 与 intake-e2e 到达 40/45 分钟 job 上限而 cancelled；同一代码的后续文档状态提交 `a331f03075c95f3b371b5a0ebd0fd91cac9dfeae` 对应 run `39090417203` 全部 job success，取消未复现。未改 CI 超时或缩减覆盖。第 1 阶段现状/影响审计已完成，清单与风险见[审计报告](../60_delivery/verification/2026-10-18--single-machine-architecture-dependency-audit-v1.md)。README 视觉素材编排已完成，只用仓库已有概念板与截图；截图素材采集/自动生成工作流继续暂停，未触发。D055 第 2 阶段 SQLite/本地内容存储已完成：隔离全链和兼容性验证通过；残留 PostgreSQL 专用 `.astext` 测试查询已改为跨库 `.as_string()`。准确代码 SHA `b0e1eb787592ff84bc4c19873a1e61cad1f9f3e6` 的 GitHub Actions run `39099573268` 为 18/18 jobs success，第 2 阶段正式关闭。第 3 阶段此前已实现并本地验收：同步处理、本地内容寻址文件存储、单一启动入口与 SQLite 默认数据目录完成；隔离 Damai 账套重置回归 2/2、SQLite schema/jobs/object-store 16/16、设置/重置 PostgreSQL 兼容回归 2/2、Ruff/mypy、文档门禁均通过；后续准确 SHA 全量 CI 通过并已关闭。整个工作包完成后再恢复知识刷新 K2。

> **2026-10-17 用户调整队列并启动 CFO 全视图实施**：用户要求立即按驾驶舱计划实施，故该项调整为唯一队首；知识刷新 K2 顺延。阶段 1–4 已完成，阶段 2 准确 SHA `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` 的 CI run `39035163288` 18/18 job 成功；阶段 3 契约代码 SHA `df5c338bc5c1d7330be2391189cdfb828099a962` 对应 CI run `39038535194` 仍在执行，其中已失败的静态 Web 与 smoke 构建发现模块图表测试 fixture 缺少契约新增的必填字段，当前分支已补齐且本地 typecheck/build 验证通过。阶段 4 页面图表、来源披露、财报行深链及九视图桌面/窄屏截图已完成；阶段 5 的浏览器 API/表格全量逐项核对、独立复核、M1、契约和相关测试已通过，当前待本轮准确 SHA 的 GitHub CI。实际截图和隔离账套证据见[浏览器验证报告](../60_delivery/verification/2026-10-17--cockpit-all-views-visual-browser-verification-v1.md)。驾驶舱工作包完成后恢复知识刷新 K2。此前 `a333b31a`、`fcfc55a4`、`c8f14b79` 的 CI 失败与修复过程保留为历史证据。

> **2026-10-16 用户续做裁决**：驾驶舱视觉与数值格式专项恢复为唯一队首（已关闭的原产品化批次保留完成状态）；范围、顺序、验收见本页队首工作项。知识刷新 K0–K6 仍排队。基线问题与隔离截图见[2026-10-16 项目复核](../60_delivery/verification/2026-10-16--project-health-and-cockpit-visual-review-v1.md)。
>
> **2026-10-17 驾驶舱视觉补全与数值格式专项完成**：代码 SHA `1a71e33fc2f779e1a848a4c3736919e98f762bdf`，准确 SHA CI run `38936413156` 全部 job 成功。本项关闭。用户随后提出新增驾驶舱图形分析与杜邦补全，本轮根据当前验收证据重新界定为“盈利能力分析与真实图表缺口补全”，不重复 51 图和已交付模块；正式设计、计划与工作包见本页队首。
>
> **2026-10-17 CFO 驾驶舱盈利分析交付**：新增 `/cockpit/profitability`，杜邦指标在显式 Objective 快照冻结时计算并记录字典指纹、行级来源轨迹和勾稽结果；只读 API 返回快照值与原始报表行深链，图表复用 ECharts。没有冻结来源或期初余额时显示 unavailable，不做隐式重算。独立复核提出的比较图单位及源行深链缺口已修复。CI 首轮发现重复 seed 时数据库归一化行 UUID 改变会制造两份新快照；修复后针对测试 10 项通过，准确代码 SHA `08aa4cd02247f995bc990d92c8f34f5a1829afa1` 的 GitHub CI run `38996089002` 为 18/18 job success。前端 36 个测试文件/184 项通过、typecheck/build 通过；后端 Ruff、mypy 通过；隔离账套核验 19/19、可见性矩阵 162 项无失败、浏览器全旅程 16/16 通过；契约检查、文档 M1 通过。实际截图、演示批次和哈希见[浏览器验收记录](../60_delivery/verification/2026-10-17--cockpit-profitability-browser-verification-v1.md)。本工作包关闭，唯一队列恢复知识刷新 K2。

> **2026-10-17 CFO 全视图阶段 2 完成**：大麦演示财务数据新增 FY2022/FY2023 六类公开年度锚点及 FY2021 期末现金锚，生成 2,304 条期间×组织×科目财务明细，严格区分披露值与 synthetic allocation；发行包 check、canonical/generator 41 项测试、隔离导入/分析回归 23 项、Ruff、mypy 与契约检查通过。标准工作簿已按生成器重建；集成测试分别验证候选状态与共享指标内容；data-contract 清理夹具先清除 ActionItem 再清理其 Finding 和 MetricSnapshot。提交 `09ba5722ec3e8075a3483223df4c81fe5cdaa9fa` 的准确 SHA CI run `39035163288` 全部 18/18 job 成功，阶段 2 正式关闭。唯一队首转入阶段 3：统一图表数据契约与聚合 API，后续任务见本工作包。

> **2026-10-17 K0/K1 完成，K2 时间门禁已到、源状态待核验**：K0 Davybase 实现 `172a099`、证据 `94fc05d`、同步 `eb8c3d0` 已推送；历史快照严格终态为 1,265 输入、1,239 成功、2 待复核、24 过滤，清单 SHA-256 `c603baab83f7873c852681c69dfb314e7004e43b230ea832fb2a1e9043ce26bc`，32 篇样本/512 张图对账通过。K1 只读扫描器实现 `a0c2e67`、证据 `a914830` 已推送；扫描 1,601 篇 Markdown、17,450 个 embed 未解析、2,445 个标准 Markdown 引用不受支持、566 篇进入人工 triage、可执行候选为 0。此结果限于 allowlist/resolver，不推断全库无原图。扫描未写入 ObsidianWiki，1,365 条 dirty 路径指纹仍一致。K1 独立审查无未解决 P1/P2。K2 冻结器已推送 Davybase 提交 `699e5c6`；独立复核发现的 `release()` 推送校验绕过已修复，13 项专项/892 项全量测试、Ruff、README 统计和断链检查通过。14:30/15:00/15:30 时间窗现已到；K2 仍为队首待启动，下一步须先只读核验 ObsidianWiki 当前分支/变更/日志，再按既有冻结器门禁决定 accepted 或 rejected。不得改动 dirty vault，门禁失败则只记录 rejected 并顺延，`CURRENT_RELEASE` 不变。

> **2026-10-16 用户四项裁决（U04 盲评复评前置）**：① **L0 挂 CI（选项 C）**——新增非阻断 `l0-baseline` job（continue-on-error），失败仅作信号灯不阻塞合并；② **盲评复评范围（选项 A）**——仅旧三样本（顺丰/腾讯/中通），新留出泛化失败归因已登记不扩大；③ **C 级维持 6 条件不变（选项 A）**——诚实标准，做不到如实 No-Go；④ **ZTO 立即恢复（选项 C）**——解封 `wip/zto-integration-20260929`。四项裁决由用户 2026-10-16 一次性给出。

> **2026-10-13 深夜·时间线迁移交付（队首子步骤二）**：演示时间线已迁移至菜鸟真实财年——比较期 FY2022（2021-04~2022-03）、分析期 FY2023（2022-04~2023-03）。canonical 明细年度聚合精确等于来源登记披露值（FY2023 收入 77,799,675 千元、毛利 8,146,656 千元，零差异）；财务报表载荷改为申请稿 IFRS 三表逐行原值（合成权益表与利息 65%/折旧 10% 等无来源行全部移除）；新增简体 IFRS 勾稽器（12 恒等式）接入发布门禁；覆盖矩阵重建为 FY2022/FY2023 各 32/50（缺口如实缺省）；ORG-LEDGER v2 重版（v1 冻结保留）。验证：报表契约 8 项、operations 16、normalization 14、enterprise 7、scripts 155、web 单测全绿；隔离栈 e2e（seed+verify+八页面 Playwright）通过；全量 API 套件该批失败已清零（route_policy 本地与 main 同败为既有环境项）。实现提交 `087a72f2`（分支 `flow/timeline-migration-20261013`）。**已合并 main（`c824f55f`，同 SHA CI 17/17 success）。F3 已完成（2026-10-14）：目录维持 v1.1 字典不新增 YAML；capex 符号语义修复（FY2023 FCF −37.3 亿如实为负）；现金流家族勾稽 + 18 项缺口族裁决测试全绿；Q1/Q2/Q3 结案。F4 已完成（2026-10-14）：环比经 prior_month 窗口由前月冻结快照真实供给（YTD 视角如实 not_applicable）；MetricCard.mom 进契约；行业分位维持缺省（经验参考≠分位分布）。批次 B 已完成（2026-10-14）：安全规格 V1.1.1（cfo 角色 + 行动项 3 Action + §10.6 四问裁决落账）、独立审查闭环、ActionItem 表/迁移/路由、双向零差集恢复（补登 cockpit overview 遗留）、web 行动项面板；§11 九类断言全绿。批次 C-2 已完成（2026-10-14）：资产负债/营运资金两模块端点+页面+导航登记，KPI 全部来自披露事实，降级块如实缺省。批次 C-3/C-4/C-5 已全部完成（2026-10-14）：费用分析/现金流/财务风险/集团合并（降级态）四模块端点+页面+导航+TSV 登记，KPI 全部来自披露事实，降级块如实缺省。**驾驶舱 8 模块页面已全量交付**（总览/利润/盈利能力由后续 51 图验收覆盖；数据中心复用现有 /data 页）。批次 D 已完成（2026-10-15）：结论条自动生成和 Findings 跨页联动已在批次 A/B 覆盖（验证通过），问数入口嵌入驾驶舱总览页（确定性 QA 入口）。**驾驶舱产品化批次 A/B/C/D 与 51 图覆盖映射已交付并关闭**；该映射不代表每个图表已在浏览器完成视觉渲染，运行时复核缺口见本页顶部引用的项目复核。随后 U04 已恢复并完成。**

> **2026-10-13 队首子步骤交付（来源登记 + 运营披露层重建）**：用户授权连续执行后，本会话在分支 `flow/source-registry-20261013` 完成两批交付并推送：① 机器可读来源事实登记 `config/damai/source_facts_v1.yaml`（325 条 disclosed_fact：FY2021–FY2023 三表逐行、FY2019–FY2025 分部序列、件量/Non-IFRS/业务线占比；原件 SHA 与页锚对 PDF 机械核验；7 项无来源假设处置登记；pytest 门禁 13 项，commit `842c8ea8`）；② `fixtures/damai/operations` 重建为披露事实层——分部序列改用菜鸟披露值（FY2025=101,272/302，FY2026 如实缺省）、件量修复数量级与语义（FY2023 国际 1,519 百万件/国内 2,311 百万单，替代旧口径 0.075 百万件）、废弃「收入÷客单价」推导（commit `e5d8d2c6`）；大麦相关 108 项测试、scripts 155 项、发行版确定性对账、m1 全绿。**当前唯一子步（新）：演示时间线迁移至真实财年**，计划见队首行。

> **2026-10-13 接手（用户确认后连续执行）**：用户确认由 ZCode 会话接手全部变更与推进，按队列连续执行、不逐项征求确认。`codex/damai-logistics-data-audit` 已全部合并进 `main`（merge commit `3b5c82b8`，文档门禁 PASS），执行位置转为 main 系分支 `flow/source-registry-20261013`，队首与队列内容不变。当前唯一子步骤仍为机器可读来源登记与数据适配设计。

> **2026-10-12 接续状态**：最新执行位置为 `codex/damai-logistics-data-audit`。F1 已完成：指标目录 v1 指纹兼容与验收时钟修复，准确 SHA CI run `38147756845` 对应 `11129263110d296f33c48b6cb94237a6fcedfd13`，17/17 全绿。F2 字典对齐、公式勾稽与测试断言修正已完成，准确 SHA `0d4b554f33bd1c9cdab3242b25d26eb2209a632c` 的 CI run `38188010174` 为 17/17 success。文档状态提交 `df0f2e6782e60d65edc955918a892c34868a9c51` 的 CI run `38188972800` 也为 17/17 success。用户于 2026-10-12 重申验收基线：全部经营数据须基于阿里/菜鸟原始公开披露，财务事实不许用无来源假设填充；大麦须被明确标为基于公开数据构建的演示主体；组织用户等非公开实体数据仅作为隔离测试夹具；全部 CFO 指标/图表/交互和全系统功能须验证，成熟组件优先。现有大麦发行包含 65% 利息拆分、10% 折旧估算等人工假设，不能作为最终事实数据源。首轮来源审计已完成，见[大麦物流来源事实与 Mock 基线审计](../60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md)：发现仓库已有可复用的菜鸟 FY2021–FY2023 三表、FY2019–FY2025 分部序列和运营指标资产，但 `DAMAI.SYN` 生成路径另造财务值并绕开这些来源；当前件量公式存在数量级和字段语义问题。**当前唯一子步骤为机器可读来源登记与数据适配设计**：复用现有 `docs/implementation/p5/cainiao_*` 事实资产，补充逐行来源 SHA/页表定位及期间口径；将披露事实、派生值、演示生成明细和隔离测试夹具分层；再重建大麦输出，明确缺失来源为 unavailable。之后继续 F3 等步骤。图表选型已采用 ECharts 6.1.0；U04 暂停至驾驶舱产品化整体完成；公开财报 C 级维持 No-Go。

> **2026-09-30 深夜·驾驶舱抢队首（用户裁决）**：用户裁决三项——① 交付形式为**真实产品页面**（Next.js 组件化 + 真实 API + `apps/web/cockpit/*` 路由，不做静态原型）；② 驾驶舱**抢在 U04 盲评复评之前当队首**，U04 转「暂停（驾驶舱让位）」；③ 第一版**用大麦物流演示数据**跑通真实链路，不等 U04 / C 级。**C 级出口状态不变（仍 No-Go），驾驶舱用演示数据不构成公开财报能力证明。** 详见下表队首行与[实施方案](../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md)。

> （接替说明）以下 2026-09-29 的队首裁决（盲评复评为队首）已被本条接替，U04 转为暂停。

> **2026-09-29 深夜·路线纠偏（用户裁决）**：用户确认 C 级 No-Go 解锁路径优先于数据扩张——ZTO 接入封存（`wip/zto-integration-20260929`），队首改为**修复后盲评复评**（C 级条件 5）；L0 挂 CI 方案待批；oracle 分批与泛化收敛随后。第 6 项 P3 暂停。

> **2026-09-29 U04 进度更新**：旧样本回归解析器与对比器修复已完成，本地 API statements 83项、脚本 unittest 155项、Ruff、mypy 203文件、plan-view、链接门禁均通过，文档 M1 通过；顺丰137/137、腾讯32/32、中通30/30，合计199/199匹配、0错配、0不可比较，产物为 `validation/financial_reports/holdout_runs/2026-09-29-adapter-v4/`。这是旧回归，不是新留出泛化通过。提交`1b313cb`准确SHA CI 中，smoke/data-contract/integration 等功能性 job 通过；`module-boundaries-e2e`测试通过，但 uv post-cleanup 因该 job 未创建 cache 目录而失败。用户批准两处最小 CI 变更（intake-e2e 超时 40→45、module-boundaries-e2e 关闭未使用的 uv 缓存）后提交 `229069ca` 准确 SHA CI run `36511316012` 17/17 success。**小米/阿里未调参首跑（run ID `2026-09-29-holdout-first-run`）双双失败**：小米 0/25、阿里 0/15，全部 not_comparable、零伪造输出，归因均为版式泛化失败（无对应适配器），登记于 [holdout-results.md §4](../implementation/objective-analysis/holdout-results.md)。按 oracle-register §4.5，用样本开发适配器即降级为回归集并启用备选 yunda/jdl 补新留出——此为下一 fork。运行器默认只选旧回归，新样本必须显式选择。常驻`flow`、`flow_test`未连接/未写入。

> 2026-09-29 最新执行进展：行身份/范围修订提交`eb2b7f3cbadec0c36eb4b36473c6321d69aa4fff`准确SHA CI run `36478301484` 17/17 success；全新隔离`flowcverify`实测 L0 1532/1532、L1 1776/1776，P5 facts 670 条内容 SHA 稳定。14份报告的样本冻结与 oracle/holdout 盘点已形成确定性清单 [`c-level-freeze-2026-09-29-v1.yaml`](../../validation/financial_reports/c-level-freeze-2026-09-29-v1.yaml) 及审计 [`公开财报 C 级样本冻结与独立验证审计`](../60_delivery/verification/2026-09-29--public-sample-freeze-oracle-audit-v1.md)。冻结测试6/6通过；报告登记和全部5份 oracle YAML 可解析，当前哈希一致。审计结论：C级 **No-Go（证据不足，不代表准确率失败）**——14份被测报告完整独立 oracle 为0/14；旧三份留出首跑199行全部不可比较；小米与阿里 FY2027Q1 新留出未发现首跑结果；既有抽取交叉评并非渲染报告盲评。原两条错误 oracle 哈希已保留历史声明并订正当前实测SHA。U04 解析与生产依赖修复提交`1b313cb`的准确SHA CI 中仅 `module-boundaries-e2e` 的 uv cache post-cleanup 失败；该 CI 收尾修正经用户批准后由提交`229069ca`完成（另含 intake-e2e 超时 40→45），run `36511316012` 17/17 success，随后小米/阿里未调参首跑已完成并登记失败归因（holdout-results.md §4）。常驻`flow`数据库/服务未触碰。

> 2026-09-28 最新更正：UX Gate1/Gate5 已关闭。Gate5 在提交`0144bad4be1a869a5a4073c516d78b4bf333cbee`完成：隔离大麦验收 verify 19/19、GET 矩阵159项零意外、Playwright 15/15；Dashboard 隔离验收 7/7；生产 E2E 157/157、Web 143/143、API mypy 203文件、typecheck/lint、文档 M1 与链接门禁通过；准确 SHA 的 CI run `36371507389` 17/17 success。常驻`flow`未触碰。唯一执行项转为公开财报 C 级归因、原件复核与抽取修订。

> 2026-09-27 最新进度（优先于下方历史快照）：八个业务页值级子项已完成。Dashboard真实下钻修复已由 `e03a1755` / CI run `36319686868` 同SHA 17/17 success。新一轮隔离验收扩展Analysis/Investigation链接身份：四问指标→指标库、财报身份→对应财报、Finding→同一分析运行→指标快照报告；verify19/19、GET矩阵159项（149×200、10×预期422、零意外）、浏览器13/13；生产E2E94/94、Web143/143、lint/typecheck通过。代码测试尚未提交/同SHA CI。覆盖与剩余链接见[Gate 1覆盖证据](../60_delivery/verification/2026-09-26--damai-visibility-gate1-v1.md)。唯一执行项仍是 UX：先同步文档、门禁、提交推送和同SHA CI，再逐项补剩余安全下钻→状态×390/1024/1440视口矩阵→Gate5最终全链同SHA验收。常驻`flow` Compose来源标签混杂，不得重启、重建或写入。更早页面子项进度只作历史，不代表当前执行位置。

> 历史快照：`/data` 与 `/investigations` 子项在 `3660389e` 收尾；当前唯一执行位置以上方最新进度及“执行队列”为准。

> 历史快照（已被首段覆盖）：`/reports`、`/data`、`/investigations`阶段验收通过；这条历史更新不再代表当前唯一执行页面或剩余工作。

> 历史快照：ORG-LEDGER `2c7d6eb4` 与 UX 页面各阶段提交、CI结果和早期状态视口材料保留在工作包及交接的历史记录中；本段原含旧页面执行顺序，当前以本页首段和执行队列为准。

> **本页是全仓唯一主线**：既维护状态真相，也维护执行队列。2026-09-25 用户裁决（2A）后不再存在第二份「唯一」文档：EXECUTION_TODO、整合总计划、统一完整实施计划与执行收敛计划均已归档为历史/参考，状态与任务只以本页和工作包为准。详细验收步骤在各工作包与参考规格。

> **测试库安全状态**：共享库误清根因已修复并于 `b60c51b` 验证：测试默认使用
> `flow_test`，常驻 `flow` 零污染。仍须保留该保护，不得将本地破坏性测试指向常驻库。

## 历史工作包登记与元数据索引（禁止从本表领取；当前状态只认下方唯一执行队列）

2026-09-28 当前状态补记（再由本页首段最新进度覆盖）：JDL原200格英文版逐格对照已完成；184格来源行/列/值匹配（含5个源表空值），16格综合收益表归属与父项语义未决。109候选比材料统计多2，保留并行核验，不阻塞后续。C级仍未通过。

| 顺序 | 工作包 | 状态 | 依赖 | 最近证据 |
|---|---|---|---|---|
| **0** ✅ | **[CFO 财务总监驾驶舱产品化（含财务指标前置）](work_items/COCKPIT--cfo-dashboard-implementation.md)** | **completed** | 大麦基础演示包 ✓（公开来源重整进行中）+ ORG-LEDGER ✓ + S01 ✓ | 批次 A、C-1、FINMETRIC F1/F2 完成；来源登记 + 运营披露层重建已交付（`842c8ea8`/`e5d8d2c6`，见 2026-10-13 交付记录）。**时间线迁移已完成（`087a72f2`）**：比较期 FY2022、分析期 FY2023、明细↔披露年度聚合零差异、IFRS 披露三表过勾稽门禁、ORG-LEDGER v2。原迁移步骤（已完成留档）：① profile/generator 月份常量与规模锚改披露值（FY2022 收入 66,866,916 千元、FY2023 77,799,675 千元，成本/毛利同步锚定，季节系数归一化保证年度聚合恒等），种植事件月份重映射；② statements.py 改由来源登记生成 IFRS 披露三表（删除 65% 利息、10% 折旧、负债/现金流拆分等无来源行，处置见登记 U-DM-*），alias map `damai_syn` 段重映射；③ FINMETRIC 覆盖矩阵按 FY2022/FY2023 重建；④ ORG-LEDGER v1 冻结包重版 v2；⑤ 测试/e2e 扫荡（44 个 FY2025/FY2026 引用文件 + 18 个月份字符串文件）、web 生产构建与快照重录、verify 19/19、全链同 SHA CI。验收：明细↔披露年度聚合对账零差异。之后再按 F3→F4→B→C-2～C-5→D 串行推进；全量 51 图表和各指标/链路须纳入最终验收。U04 暂停至本工作包整体完成；**不解除 C 级门禁**。[审计记录](../60_delivery/verification/2026-10-12--damai-source-baseline-audit-v1.md) · [实施方案](../superpowers/plans/2026-09-30-cfo-cockpit-implementation-plan.md) |
| 0a | [财务指标目录（驾驶舱前置）](work_items/FINMETRIC--financial-metric-catalog.md) | **completed** | 指标引擎 + 会计科目基础 ✓ | F1/F2 已由准确 SHA CI 关闭；F2 覆盖矩阵 FY2025 42/50、FY2026 45/50，准确 SHA `0d4b554f33bd1c9cdab3242b25d26eb2209a632c` / run `38188010174` 17/17 success。F3/F4 未启动，先完成 CFO 队首内的数据来源与 Mock 基线重整。[工作包](work_items/FINMETRIC--financial-metric-catalog.md) |
| 0b | [CFO 全视图数据与图表完整性改造（旧工作包）](work_items/COCKPIT--all-views-data-and-visual-completion.md) | **archived** | 已由 7a 队首接替；禁止独立执行 | 九页/25 图本地验收保留为回归基线；`39042517573`、`39041228479` cancelled，`39040652008`、`39038535194` failure，准确 SHA CI 未通过。|
| 7a | [单机原型架构简化与全视图视觉升级](work_items/FLOW--single-machine-visual-prototype.md) | **completed（2026-10-24）** | D055 已确认；工作包已通过 7a.1–7a.8 结案 | PR #3 merge commit `b2a1bf22df91239eb311d1692c30c666250678bf`，CI run `40092106547` 为 28/28 success。原型交付和限制见[完结差距审查](../60_delivery/verification/2026-10-24--prototype-completion-gap-review-v1.md)；工作包已 `do_not_execute: true`。|
| 1 | [U08 生产就绪收口](work_items/U08--production-readiness.md) | **completed** | — | U8-A～D 完成；严格 HTTPS/双格式 SHA/恢复门禁通过；冻结记录与标签 |
| 1' | [U04 独立 oracle](work_items/U04--independent-oracle.md) | **completed** | 样本冻结已完成 | 驾驶舱批次 A 完成后，用户要求继续完整驾驶舱实现；因此盲评复评暂停至本工作包整体验收，不是取消。完整独立 oracle 与报告盲评仍是 C 级证据门槛 |
| 2 | [S01 战略边界、事实合同与安全门禁](work_items/S01--post-u8-boundary-contract-security.md) | **completed** | U08 completed | Task 1–5 完成；安全规格 V1.1 已批准且独立审查闭环（`6c3c1cd`，零 P1/P2）。2026-09-14 `ff42c67` 五路并合 + 回落修复（`c1510ce`→`2570bf8`）带入路由策略 v2、模块边界与 U8 升级门禁、迁移 0026 修复、`main.py` 启动 fail-fast、两模块入口；Kimi `0841ff9` v1 被否，由 `997c1ab` v2 取代。**Task 6 已关闭**（R2/R3/R4 交付，台账 §7），阶段 3 转入 C 级出口；[协调台账](../70_operations/2026-09-14-coordination-ledger-glm.md) / [范围计划](../superpowers/plans/2026-09-13-flow-post-u8-boundary-gate.md) / [并行执行计划](../superpowers/plans/2026-09-13-flow-three-agent-parallel-restructuring.md) |
| 2a | [大麦物流完整财年演示数据](work_items/DAMAI--full-year-demo.md) | **active（按用户新标准重开；CFO 队首子包，不另列任务）** | 已批准规格；不依赖公开 C 级 | D1–D3 旧版已集成 main `e22d193`，CI run `36137591750` 17/17；原隔离栈验收证据保留。用户 2026-10-12 新增来源事实要求后，旧包仅作为基础夹具完成；需在 CFO 唯一队首中重建来源登记、转换血缘及假设值处置，不与 CFO 并行执行 |
| 2b | [大麦数据后的剩余体验收口](work_items/UX--post-damai-experience-closeout.md) | **completed** | G2 ✓；用户已批准；ORG-LEDGER CI ✓ | Gate1/Gate5关闭：隔离 Dashboard 7/7；大麦验收 verify19/19、GET矩阵159项零意外、Playwright15/15；生产E2E157/157、Web143/143、mypy203文件、typecheck/lint、M1/链接检查通过；提交`0144bad4`同SHA CI run `36371507389` 17/17 success。常驻库未触碰。 |
| 2c | [企业组织建制与经营账套初始化包](work_items/ORG-LEDGER--enterprise-initialization-package.md) | **completed** | 大麦发行包 completed；批准三表 schema | `2c7d6eb4`；CI run `36270782272` 的17/17 jobs success。隔离 `full` 首次/重复与 `business` 对账通过；11 个企业/loader 测试、全量 API 852、Web142、脚本107、大麦 verify19/19、API43/43、Playwright9/9、合同/文档/lint/typecheck 均通过。31文件 manifest 稳定 SHA `cbc7cccf…e513`。 |
| K | [第二代静态知识刷新与战略重基线](work_items/KNOWLEDGE--refresh-v2.md) | **active（K3 全量语义路由）** | K0–K2 完成；HIGH/MED/LOW审阅与错误集中度复核已完成 | 9,673个来源：routed 415、filtered 176、pending_review 9,082。全量路由至第091批；6条待核、6条企业内部或范围外来源过滤。华为经营分析文章17条图片引用未解析，不据图推断；5个locator-only例外继续待审，不使用范围外内容或链接标题推断。下一批第092批；随后完成coverage闭合、知识综合、独立reader与结案门禁；`CURRENT_RELEASE`不变。详见工作包。 |
| 3 | [公开财报模块 C 级出口](work_items/PUBLIC--c-level-exit-protocol.md) | **active（C级门禁未通过）** | 行身份修订与样本冻结 ✓ | 本轮证据审计已作 No-Go（证据不足，不是准确率判负）；当前队首转入 U04，C级仍无14份完整独立 oracle、新 holdout 首跑及成品盲评 |
| 3a | [溯源/重述/只读 MCP](work_items/PUBLIC--provenance-restatement-mcp.md) | **completed** | — | B3 溯源 95.5% 行项目带页锚（迁移 0029 + 导入/API/前端）；B4 supersedes 链 + 差异脚本；B5 只读 MCP 三工具（token fail-closed）；B6 确定性差异说明起草 |
| 3b | [数据扩张、行业基准与 10× 性能基线](work_items/PUBLIC--data-expansion-benchmarks.md) | **active（队列排队，不并行启动）** | 性能基线 ✓；扩张待外部财报 | G2 完成：10×（1034→10340 行）P95 明细 6.2ms/检索 0.97ms/聚合 1.11ms（`perf_baseline.py`）；C1 扩张需真实财报到料 |
| 3c | [AI 问数 v1 与评测集](work_items/PUBLIC--ai-qa-v1.md) | **completed(v1)** | — | 确定性检索引用 QA + 94 问评测集（60 数值 + 34 拒答）命中率 100%、拒答零误答（`ask_facts.py` / `generate_qa_eval.py`）；LLM 通道与 v2/v3 另行裁决 |
| 3d | Web 前端一致性整改（信息架构/设计 token/组件库/五态/响应式） | **completed** | — | P0–P3 五批：`fe61b5c`（F2 token+值漂移）→ `8fa13a6`（生产构建门禁+溢出修复）→ `53ef2eb`（数据态门禁+触控+溯源交互）→ `defd823`（PageState+FlowDataTable+两页迁移）；P4–P5 四批（2026-09-18）：`0c4c45a`（metric-library 深度迁移）→ `b7b4257`（investigations 详情）→ `3089472`（Task 8 切片）→ `9cf8cb3`/`02c11ea`（frontend-states 状态门禁+60 图状态矩阵归档）；门禁矩阵 390/1024/1440 × 数据态 × 加载/错误/403，生产 e2e 69/69、单测 86/86、lint 1 登记例外；Task 0–9 全关闭，执行日志见[整改计划 §10](../superpowers/plans/2026-09-16-frontend-consistency-remediation-plan.md)。遗留（不阻塞）：溯源真实来源链接（已按公开来源政策解锁，见 HANDOFF v3.3 §2.3） |
| 4 | 企业内部月度工作台 | **gated(C 级出口 + 数据授权)** | 公开 C 级 + 授权 | 持续企业空间、月度周期、Finance BP 轻量提交、双版本报告。设计输入已备：知识库第二截面登记经营分析会四体系/月度周期蓝本与月报可视化实例（借鉴 #20/#22/#24，[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)）；AR 应收信用子域知识（科目/口径/账龄五桶/催收与信用规则，借鉴 #26，[FinBoss 评估册](../knowledge-base/02_research/synthesis/2026-09-19-finboss-assessment.md)——整理性质，行业参考值待溯源） |
| 5 | 四级验证 | **gated(内部工作台可用)** | 内部工作台 | 连续 3 个真实月度周期、同输入人工基准、逐周期盲评与 20% 工时门槛；[验收 §14.2](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md#142-最终真实企业验证协议) |
| R1 | [U09+O05 授权内部试点](work_items/U09-O05--authorized-internal-pilot.md) | **blocked（依赖/证据门槛，不等用户授权）** | 公开 C 级 + 可用真实企业数据 | 用户已授权执行；轮到后先用可用数据完成技术试点。无真实企业数据时形成明确的未验证结案，不把合成数据冒充真实试点 |
| R2' | [U10 V1.1 证据决策](work_items/U10--v1-1-evidence-decision.md) | **blocked（依赖证据门槛，不等用户授权）** | U4 + U8 + U09/O05 | U8 已完成；轮到后整理现有证据、逐项给出有依据的 go/hold，不因待证据项停止其他执行 |
| D1 | [DOC-M5/M6 文档迁移](../superpowers/plans/2026-09-12-static-knowledge-and-document-migration.md) | **done**（bfc1271 / e373e25） | — | M0–M6 全部关闭 |

## 唯一完整 To-do 与执行队列（严格串行）

**统计口径：16 个唯一事项；已完成 10，实际执行中 1（K/K3），队首待启动 0，排队 3，暂停 1，外部条件受限 1。** 视觉语言工作包已结案；事项 13 的并行例外已关闭，15 个已合入 main 的历史分支已删除，保留 main、开放 PR #5 分支与暂停的 ZTO 分支；历史 K 仍是 7 的别名，不重复计数。

| 原编号 | 唯一事项 | 当前事实状态 | 证据与处理边界 |
|---|---|---|---|
| 12 | [可复用视觉语言提炼与 FLOW 全项目视觉统一](work_items/FLOW--portable-visual-language-and-full-project-restyle.md) | **completed（2026-10-26；原生 200% 外部条件受限结案）** | [视觉语言设计规格](../superpowers/specs/2026-10-24-flow-visual-language-system-design.md)；20 路由、图表、导出、README 与可复用资产均完成；200% 原生缩放待设备/工具条件恢复后补验 |
| 13 | [清理已合入 main 的历史远端分支](work_items/FLOW--merged-branch-cleanup.md) | **completed（2026-10-25）** | 15 个旧分支经逐支 SHA、祖先与开放 PR 复核后分三批删除；远端仅保留 main、开放 PR #5 的视觉分支和暂停的 ZTO 分支。未改 main、未重写历史 |
| 0 | CFO 盈利分析与图表补全 | 已完成 | 四因子、冻结值、来源深链；`08aa4cd0` 准确 SHA CI 18/18；新验收由 7a 承接 |
| 0a | 驾驶舱数值格式治理 | 已完成 | 整数订单、金额两位小数；`1a71e33f` 准确 SHA CI 通过 |
| 7a | 单机原型与全视图视觉升级 | **已完成** | PR #3 merge commit `b2a1bf22df91239eb311d1692c30c666250678bf`；run `40092106547` 为 28/28 success；交付限制见验收报告 |
| 1 | 组织与经营账套初始化包 | 已完成 | 历史 full/business 重置、幂等/隔离和发行验证；最终 SQLite 操作由 7a.6 复验 |
| 2 | 大麦数据后体验收口 | 已完成 | `0144bad4` 准确 SHA CI；新视觉由 7a 承接 |
| 3 | 公开财报样本/证据审计 | 已完成（No-Go 审计） | 证据不足裁定已交付，不代表 C 级通过 |
| 4 | U04 解析与盲评复评 | 已完成（限定样本） | 旧三样本 199/199，不等于全部报告 oracle 完成 |
| 5 | C 级质量基准与 Go/No-Go | 已完成（裁定 No-Go） | 部分条件后续已有改善，仍无整体验收 Go |
| 6 | P3 真实数据/来源与行业扩张 | 暂停 | 历史 ZTO 封存已于 2026-10-16 恢复合并，不重复合并；其余扩张暂缓 |
| 7（原 K） | 第二代静态知识刷新 | **进行中：K3 全量语义路由与 coverage 闭合** | registry/baseline 与 9,958 ID 累计 diff 已复验；HIGH 全文、MED/LOW 双审和错误集中度复核已完成。全量路由至第091批，coverage 9,673条（routed 415、filtered 176、pending_review 9,082）；5个locator-only例外保持待审；下一步第092批，之后完成知识综合、独立 reader 与结案门禁；CURRENT_RELEASE 不变 |
| 8 | rnd_exp 官方依据核验 | 外部条件受限 | 已有来源基线处理记录；轮到后恢复检索或附原文不可得证明结案，不伪造核验 |
| 9 | U09/O05 真实内部试点 | 排队 | 需要真实企业数据及质量门槛；技术原型不冒充真实试点 |
| 10 | U10 V1.1 证据决策 | 排队 | 依实际证据 go/hold，不作为原型的无限开发项 |
| 11 | 内部月度工作台与真实周期验收 | 排队 | 真实连续 3 个周期、人工基准、盲评与工时比较；模拟数据不能替代 |

### 7a 单机原型收尾动作与完成条件（2026-10-24）

**2026-10-24 连续执行授权：** 用户要求开启一个专门收尾任务，连续完成本节可做动作后进入收尾，不再反复计划或扩展范围；遇长等待或外部依赖允许跳过。由新任务接管既有工作树 `/Users/qiming/workspace/FLOW/.worktrees/cockpit-visual-completion` 和 `codex/single-machine-runtime-convergence`，本会话完成交接后不再并发写入。主目录旧分支与未提交文件保留原位。

**执行与跳过规则（本次用户授权优先于旧“不得跳项”条文）：**

- 正常情况按 7a.1→7a.8 串行持续执行；常规可逆选择由 Agent 自行采取推荐方案，不逐项索取确认，不以阶段汇报结束整个任务。
- 对外部等待、服务不可用、真实数据缺失或超出本原型边界的能力，先做一次有针对性的诊断和一个安全替代尝试；连续约 15 分钟没有可执行进展时登记“跳过/未验证”、证据、影响与恢复条件，继续下一可独立完成动作。15 分钟为处置参考，不强行终止仍在产生有效输出的构建/测试。
- CI 排队或约 20 分钟以上的远端检查不阻塞其他本地实现；保留真实 run/SHA，继续独立动作。最终可做一次有界状态核对，不反复重跑、不为等待 CI 空耗会话；未结束/失败的检查不得宣称通过。最初接手时，计划提交 `6757b4b6` 的 run `40075162854` 仍执行中；现候选 SHA `0a43d131d44a5891181b2e935e011888b3101660` 的 run `40079923908` 已 28/28 success。
- 关键财务计算、数据真实性、数据隔离和来源链的已证实错误仍须修复；无法安全修复的非核心功能明确禁用/说明限制。核心旅程若仍受影响，只能作“有保留交付/未满足项”收尾，不伪装成完整验收。
- 删除、密钥/环境文件、未授权 CI 配置或 schema/迁移等红线不能用跳过规则绕过；先保留现状/采用不触线方案并继续其余动作，只对确实无法替代且必需的动作集中请求授权。
- 收尾时一次性交付已完成清单、跳过清单、可运行入口、静态包、验收结果和准确 SHA；暂缓的知识刷新、真实企业试点、扩行业等不自动恢复。本版不得因新增竞品功能或“还可美化”再次重开。

本表曾是 7a 唯一可领取子步骤，现已全部结案；不在审查报告、工作包或交接复制第二份 To-do。**7a.1–7a.8 均已完成；main merge commit `b2a1bf22df91239eb311d1692c30c666250678bf` 对应 run `40092106547` 为 28/28 success。K2 已成为队首待启动事项，但本轮未自动开启。** 新的 CI 配置、数据库迁移、删除仍遵守授权红线。

**工程量估计：单写者连续投入约 6–10 个有效工程日，包含修复和复核；不承诺日历日期，也不含新的真实数据到料/外部审批。** 7a.1 提供现有可打开预览，7a.4 提供新版视觉预览，7a.8 提供正式版本与静态包。新缺口只修影响以下完成条件的 P1/P2，不自动扩张范围。

| 动作 | 目的与交付 | 主要文件/复用对象 | 通过条件 | 估计 |
|---|---|---|---|---|
| **7a.1 统一交付基线** | 已完成：核对 main/开发分支双向差异、主目录 4 个修改与 1 个未跟踪文件；确定候选与批次 | [基线复核补记](../60_delivery/verification/2026-10-24--prototype-completion-gap-review-v1.md#7a1-基线复核补记2026-10-24)、现有离线预览 | 主目录文件原位保留；候选为 `191cddd3` worktree，Damai v2；旧预览仅历史总览 | 完成 |
| **7a.2 补齐已有演示数据的 CFO 呈现（已完成）** | 冻结页面—指标—数据—图表矩阵；接通预算执行、合成账龄、利润桥/产品毛利入口 | `cockpit/modules.py`、`cockpit/service.py`、`dashboard/service.py`、`cockpit-overview-visuals.tsx`、`module-page.tsx`；既有总览组件、canonical 只读 | 图/表/来源同值；合成与披露分区；账龄总额按自身余额口径对账；已有数据无无解释空洞；缺预测/抵销/概率事实时清楚说明 | 1.5–2.5 日 |
| **7a.3 接通图表、筛选与追溯（已完成）** | 点选/触屏和键盘等价表格进入指标/明细/来源；筛选可选名称；年度固定图与月度筛选边界明确 | `charts/echarts-base.tsx`、`charts/builders.ts`、`module-page.tsx`、`drill-drawer.tsx`、`cockpit-filter-bar.tsx`、`cockpit-overview-app.tsx`、`lib/deep-links.ts` | 每种核心图型至少一条真实点选到明细；关键值到定义/输入/来源全链；URL 刷新/后退恢复筛选；无伪链接和不适用维度合计；键盘可达 | 1–1.5 日 |
| **7a.4 收敛 A+C 视觉（已完成）** | 总览桌面/手机定基准，推广六主题/杜邦/数据中心，巡检其余页面 | `cockpit.css`、`kpi-card.tsx`、`cockpit-overview-visuals.tsx`、`module-page.tsx`、`profitability-page.tsx`、workflow-nav、shell/data 与支撑页样式 | 1440×1000 首屏有四核心 KPI、主趋势和现金桥有效图形区；辅助指标/来源/设置不挤压主图；九重点页 390/1440px 无溢出；20 路由模板无明显样式断层；图例/标签/期间清楚 | 1–2 日 |
| **7a.5 图文报告与九页离线包（已完成）** | 复用冻结快照发布 HTML/PPTX/XLSX；九重点页静态索引、图像/图表、同值数据和来源清单绑定同一版本 | 现有 publishing renderers、报告中心、`scripts/export_cockpit_snapshot.mjs`、截图索引 | 导出数值与冻结快照一致；离线无外网依赖、内部静态导航有效；动态操作说明清楚；PDF 后端未配置时明确不可用且可浏览器打印，不虚报成功；图片/API/候选/批次一致 | 0.5–1 日 |
| **7a.6 单机数据操作入口（已完成）** | 复用 loader/reset/backup，提供显式演示装载、business 重置、备份、新目录恢复、校验命令；配置端口和清楚故障提示 | `scripts/flow.py`、`Makefile`、`infrastructure/local_backup.py`、`fixtures/damai/{loader,reset}.py`；新增隔离验收入口/定向测试 | 初始化/装载/重启一致；business 只动指定企业经营数据且组织/系统保留；full 模式兼容但不自动执行；恢复后来源/图表/报告一致；普通运行和新验收无需 Docker/PostgreSQL/Redis/MinIO | 0.5–1 日 |
| **7a.7 最终隔离验收与独立复核（已完成）** | 冻结代码候选；SQLite 全业务旅程、数值/图表、桌面手机、缺数/失败态、离线和恢复；新上下文独立评审；准确 SHA 全量 CI | navigation/damai-demo/deep-links E2E、cockpit/SQLite/local-store 测试、新单机闭环入口、现有全量 CI | verify 19/19（扩展须说明新增契约）、核心值零不明差异、20 路由模板/九重点页覆盖、离线外部请求/错误均 0、无未修 P1/P2、准确 SHA CI success；不以旧库 CI 代替 SQLite 旅程 | 0.5–1 日 |
| **7a.8 主线集成与交付归档（已完成）** | 回流 main 有价值文档；创建可审阅 PR，按已有授权/保护规则集成；提交最终说明、验收总表、版本/数据/演进清单及恢复档案 | README、HANDOFF、PROJECT_STATE、本路线图、现有文档/图片索引、Git PR、最终静态包 | 正式交付指向 main 准确版本/CI；新环境能按说明启动；交付物可打开；文档无过时进行中；历史/决策/操作知识可恢复；全部通过才关闭 7a，不宣称长期目标已达成 | 0.5 日 |

#### 实施细节与验证约定

路径约定：上表前端组件简称均在 `apps/web/components/`，其中驾驶舱在 `cockpit/`；后端模块在 `services/api/src/flow_api/`。7a.2 复用 `apps/web/components/dashboard/profit-bridge-panel.tsx`、`product-performance-table.tsx`、`margin-matrix.tsx`；7a.5 修改 `apps/web/components/reports/reports-center.tsx`、`reports-center.css` 及 `services/api/src/flow_api/publishing/{renderers,objective_renderers}.py`。7a.6 拟新增 `scripts/test_single_machine_closeout.py` 和 `scripts/tests/test_flow_cli.py`；7a.7 通过新 `make flow-check` 执行隔离 SQLite 浏览器旅程（此入口当前尚不存在）。测试复用 `apps/web/tests/cockpit-overview-visuals.test.tsx`、`apps/web/tests/components/cockpit-module-page.test.tsx`、`apps/web/e2e/{navigation,deep-links,damai-demo}.spec.ts` 及 `services/api/tests/cockpit/test_modules.py`；仅为真实行为缺口加断言，不复制实现。API 参数或响应变化时同步 OpenAPI/TypeScript 契约并执行 `make contracts-check`。

- **7a.1：** 使用 `git log --left-right --oneline origin/main...HEAD`、`git diff origin/main HEAD --stat`，并只读核对主目录精确四文件差异。不自动 stash、删除或覆盖；main 内容做语义回流，不把旧状态覆盖新状态；最终普通 merge/PR，不 rebase/强推。实际共享写入冲突才暂停相应目标。
- **7a.2：** 先核验现有预算/应收的期间、单位、维度、事实类别和加总基准；为投影/图表同值的实际缺口加定向测试再接线。复用 `/` 已有利润桥、产品表、毛利矩阵，不建第二个公式引擎。账龄与公开应收行不同口径时不强行勾稽。合并页缺抵销数据时校准标题/说明；月度收入预测不改名为 13 周现金预测。
- **7a.3：** 点选传既有 period/metric/source ID 到现有深链，不从坐标反推事实。显式值表共用同一映射；有 fact ID 但无原件时解释缺失。年度补充区明确不随内部组织/客户筛选变化；需要联动时由经核验 API 提供同范围数据，不前端拼接。
- **7a.4：** 核对[概念板](../assets/cockpit-visual-direction-2026-10-18.png)六个签名：暖纸白、墨蓝、古金、衬线标题、图表主次面积、结论/来源/行动叙事。保持语义红绿和实际负数。图表都有标题、期间、单位、事实类别、支持值/来源；状态覆盖 loading/empty/error/ready/degraded。复用 ECharts/现有表格，不引新图表库，不加装饰性伪数据图。
- **7a.5：** 先检查导出图像和 API 是否同批/同期间；输出到独立目录，manifest 记录 full SHA、数据包 SHA、批次/快照、视口、事实类别和限制。静态链接指向静态目标。使用已授权的本机验收截图能力；GitHub/README 自动采集工作流保持暂停，不新造截图管线。
- **7a.6：** 已提供 `make flow-demo`、`make flow-demo-reset ENTERPRISE_ID=...`、`make flow-check`、`make flow-backup BACKUP_PATH=...` 和 `make flow-restore BACKUP_PATH=... RESTORE_DIR=...`。命令使用隔离 `FLOW_DATA_DIR`，restore 写入新目录；seed/reset 不混入普通启动。端口同步传 Web 内部 API、健康检查和地址输出。验收使用新隔离目录/空闲端口，不停常驻服务。
- **7a.7：** 每切片执行相关 Vitest/API pytest 与 typecheck，视觉/交互完成再做 production build/浏览器，最后完整冻结验收。现有命令：`pnpm --filter @flow/web test`、`pnpm --filter @flow/web typecheck`、`pnpm --filter @flow/web build`；后端定向执行 cockpit、local_object_store、sqlite_schema 测试，先核对 fixture，临时 SQLite 与隔离 PostgreSQL 分开。浏览器指向隔离服务 PLAYWRIGHT_BASE_URL；旧 user-closure 脚本会调用 infra-up，不能拿来证明无 Docker 的单机验收。
- **7a.8：** 运行 `python3 scripts/check_docs.py --phase m1`、`--phase m6`、`python3 scripts/documentation/links.py --check`、`git diff --check`；不新增 release 服务。归档保留版本、演进时间线、决策、操作知识和恢复入口；文件/历史删除、CI/schema 改动仍按原红线授权。审批确有限制时保留可验收候选、PR 与明确限制，不隐去未集成状态。

7a.7 冻结最终代码候选后，必须重验 7a.5 静态包/图片 manifest；若 7a.6 等后续代码改变页面、数据或导出行为，重新生成受影响交付物再核验。纯文档提交可保留明确标注的实际采集代码 SHA，不能把旧图片改标为新版本。

#### 当前版本的结束判定

8 个动作逐项附证据后交付五件可直接使用的成果：**正式 main 版本、本机启动/数据操作说明、大麦演示包、九页静态展示/图文报告包、同版本验收与恢复档案**。仅以是否违反本节验收条件决定追加修复，不以“还可以美化”无限延期。长期知识刷新、行业扩张和真实试点继续保留，不自动启动来延长本原型结案。

<details>
<summary>历史队列全文（2026-10-21 及以前；冻结参考，禁止独立执行）</summary>

以下保存演进依据，旧 K/7 重复、旧计数及待验证文字由上方 2026-10-24 队列接替，不作为当前进度。

**当前唯一队列（15 项）**：已完成 8 项；实际执行中 1 项（7a，视觉差距收敛与文档审查）；队首待启动 0 项；排队 4 项（含 K3）；暂停 1 项；外部条件受限 1 项。代码 SHA `65d7dc61` / run `39453419044` 因状态更新提交而取消，汇总 job 失败仅反映分片取消；状态提交 `a71cb28e` / run `39453752316` 已 28/28 success；最新文档 SHA `21b650a1` / run `39457446117` 已 28/28 success。移动 KPI 修复由隔离 fixture E2E 21/21 验证；本地期间费用堆叠图由 Web 199/199、typecheck/build 验证。准确 SHA `a71cb28e` CI 28/28 success；lint 0 error、文档 M1/M2/M6 通过。原 `integration` 基线用时 36分51秒；新结构按 4 个隔离 shard 保留全量 284 项测试，66 文件映射零遗漏、零重复，准确 SHA `368a0190` / run `39349190031` 为 28/28 success。单机架构继续采用 SQLite、本地文件、同步处理和一键启动；本轮无依赖、服务或数据库变化。剩余为文档审查/清理候选复核、独立复核及最终准确 SHA CI。唯一顺序见[工作包第 9 节](work_items/FLOW--single-machine-visual-prototype.md#9-概念图视觉差距门禁负载与文档治理)：全视图视觉差距闭合 → 文档现状校准与清理候选复核 → 最终集成结案。

0. **completed** [CFO 驾驶舱盈利分析与图表缺口补全](work_items/COCKPIT--visual-analysis-expansion.md)：四项指标于 Objective 快照冻结并存 trace；只读 API；杜邦树与两期比较图；指标/财报/来源行深链；未具备口径时 unavailable。范围与交付记录：[设计规格](../superpowers/specs/2026-10-17-cfo-cockpit-visual-analysis-expansion-design.md)、[实施计划](../superpowers/plans/2026-10-17-cockpit-visual-analysis-expansion.md)。
0a. **completed** [驾驶舱视觉补全与数值格式治理](work_items/COCKPIT--visual-completion-and-number-format.md)：订单/件量整数、金额两位小数、单位格式统一、费用页错误修复、真实图表/趋势/下钻、8 页面截图及隔离浏览器验收；代码 SHA `1a71e33f`，准确 SHA CI run `38936413156` 全部 job 成功。
7a. **active（视觉差距收敛与文档复核进行中）** 单机原型架构简化与全视图视觉升级：阶段 7冷启动 19/19、离线快照零网络请求通过；最新已核对的准确 SHA `21b650a1` 的 CI run `39457446117` 为 28/28 success。当前分支含暖纸白/墨蓝/古金样式、ECharts 配色与四分片集成门禁；全量测试映射为 284 项、66 文件、零遗漏/重复。视觉尚未达到概念图报告密度和图表层级，当前必须继续逐视图收敛；单机架构验收已完成，最终复核继续确认没有遗留的无用运行依赖。截图与本轮范围见[阶段 7验收记录](../60_delivery/verification/2026-10-20--single-machine-visual-static-acceptance-v1.md)及[工作包第 9 节](work_items/FLOW--single-machine-visual-prototype.md#9-概念图视觉差距门禁负载与文档治理)。
K. **queued（待 7a 阶段 5–7）** 第二代静态知识刷新与战略重基线：K0/K1/K2 已完成，K3 baseline/diff 已生成并复验。语义路由、HIGH 全审、MED/LOW 双审、coverage 闭合、候选与独立 reader 尚未完成；不得将自动登记冒充语义审阅。ObsidianWiki 保持只读，`CURRENT_RELEASE` 不变。

以下 1–11 是驾驶舱队首调整前的原队列事项：1、2、3、5 已完成；4 U04 与 6 P3 暂停；7、9、10、11 排队；8 外部材料受限。旧验证记录仍是历史证据，不代表当前执行位置。

2026-09-28 执行进度：UX Gate1/Gate5 已在`0144bad4`完成并由准确 SHA 的 CI run `36371507389` 17/17验证通过。C级只读来源基线审计提交`f1ab4283`对应CI run `36375305428` 17/17 success。JDL页界限修复提交`5c84c81fdd3c0908891d16f8dcfe05e1d2e64b6c`对应CI run `36382657675`准确SHA 17/17 success。隔离Compose栈迁移0031并装载14份报告，L0 1508/1508，L1 1775锚零失配；财报测试76项、脚本测试110项、M1、链接、定向ruff及shell语法通过。唯一下一子步为建立42异常/109口径疑点/JDL原200格的规范化逐格台账并逐项复核原件。常驻`flow`不写入/清理/重启/重建。

2026-09-29 最新更正：109格语义裁决和其后行身份/范围修订及全链验证已完成。新的 L1 v5 覆盖1776/1776；独立 `flowcverify` 全新隔离栈装载14份报告后 L0 1532/1532、L1 1776/1776，P5事实670条内容SHA不变。C级仍未通过。下一唯一子步为冻结样本/证据清单并核验尚未闭合的独立 oracle、盲评和 holdout；交付后作 Go/No-Go。常驻库未写入。

截至 2026-09-29：**11项，已完成3项，唯一执行中1项，排队7项**。第3项的样本与证据审计已按现有材料作 No-Go 结案；产品 C 级出口本身仍未通过。第4项 U04 的旧三样本版式回归已实现199/199，生产依赖修复已推送。准确SHA CI 的功能性 job 全绿，但模块边界 E2E 作业的 uv cache post-cleanup 失败（Playwright 测试成功）；由于修复会改 CI 配置，需先取得用户批准。批准前不读取小米/阿里抽取结果、不标记 CI 通过。常驻`flow`不写入/清理/重启/重建。

1. **[完成] 企业组织建制与经营账套初始化包**（工作包见状态表2c）：提交 `2c7d6eb4`，CI run `36270782272` 的17/17 jobs success。31文件发行包稳定 manifest SHA `cbc7cccf…e513`；隔离 `full` 首次/重复、`business` 重置及回滚/租户隔离通过；全量 API852、Web142、脚本107、verify19/19、只读 GET43/43、Playwright9/9，合同/文档/lint/typecheck均通过。仅三表迁移在隔离栈验证，未触碰常驻库。
2. **[完成] UX 可见性与全站验收关闭**（工作包见状态表2b）：Gate1/Gate5证据与准确SHA CI已收口，见上方最新状态和工作包最终关闭记录。

3. **[完成—证据审计 No-Go] 公开财报 C 级样本/证据盘点与当前门禁裁定**：冻结14份 PDF/YAML、报告身份映射、行身份修订表、L1 v5、实现 SHA；哈希确定性重建测试6/6。审计证实14份报告没有完整独立 oracle；5份既有 holdout oracle 均为部分转录，两个新留出尚无首跑结果；旧首跑199行全部不可比较；现有交叉评不是成品盲评。故本阶段 C 级判为 No-Go（证据不足），详见[冻结与 oracle 审计](../60_delivery/verification/2026-09-29--public-sample-freeze-oracle-audit-v1.md)。这不是 C 级通过，剩余证据工作继续由第4、5项承接。
4. **[完成·盲评复评 199/199] U04 解析器适配与独立留出验证**（工作包见状态表1'）：顺丰文本型“合并及公司”、腾讯财报表格动态定位、中通公告重复字形解析，以及 comparator 列名/报表范围已修复；旧三样本回归199/199，见 adapter-v4。初始 smoke 缺包原因已定位为`pypdf`仅列dev组，现已移至生产依赖；独立 Compose 验证API/Web健康、迁移和dev主体seed成功。CI 收尾修正（`229069ca`，含 intake-e2e 超时 40→45 与 module-boundaries uv 缓存关闭，均经用户批准）已全绿：run `36511316012` 17/17 success。**首跑已执行**（run ID `2026-09-29-holdout-first-run`，输入/代码/oracle SHA 与完整机器 diff 已保存，人工介入 0）：小米 0/25、阿里 0/15，全部 not_comparable，零伪造输出；归因均为版式泛化失败（无对应适配器），见 holdout-results.md §4。**U4 已按范围关单（2026-09-29 深夜）**：①旧回归 adapter-v5 199/199 零退化；②小米/阿里适配器开发完成并按 §4.5 降级回归集（适配后回归 24/25、15/15+勾稽一致）；③备选 yunda/jdl 先冻结+oracle 后首跑：yunda 0/20（A 股适配器缺口）、jdl 0/25（显式降级），失败原始保留、身份保持留出；④泛化缺口登记为第5项裁决输入。关单提交链 `4f997020`+`a28b638d`（static-python 修复），准确 SHA CI run `36525496607` 17/17 success，**U4 正式关闭**。细节见 holdout-results.md §5 与 U04 工作包。不能由实现方代替独立录入/盲评。
5. **[完成·No-Go 裁决] C 级质量基准与 Go/No-Go**：当前 HEAD `3b2d130f` 隔离栈 `flowcgo` 重跑 L0 1532/1532、L1 1776/1776 零差异并归档；§3 六条件对账裁决 **No-Go**（条件 1/2/4/5 未满足：L0 未进 CI、完整 oracle 0/14、泛化层留出失败、盲评复评未做；条件 3/6 达成）。裁决文档与四步解锁路径见 [2026-09-29 C 级基准重跑与 Go/No-Go](../60_delivery/verification/2026-09-29--c-level-benchmark-rerun-gonogo-v1.md)。**用户路线纠偏裁决（2026-09-29）**：解锁路径重排为——①盲评复评（队首，条件 5）；②L0 挂 CI（条件 1，方案待批）；③oracle 分批/泛化收敛（条件 2/4）；④数据扩张（原第 6 项）暂停。
6. **[暂停·用户裁决 2026-09-29] P3 真实数据、来源与行业扩张**：ZTO 接入已完成大半（产品 YAML 57 行与 oracle 逐值一致、L1 答案集 v6 1823/1823 全锚定、隔离栈 L0/L1 实测零差异），按用户路线纠偏裁决**封存**于分支 `wip/zto-integration-20260929`（`2ce0700e`），未完成 API/UI 链路与文档同步。恢复条件：C 级解锁四步完成后或用户重新指令。阿里分部序列复核与 C1 扩张随本项一并暂停。
7. **[排队] 第二代静态知识 release 与战略重基线**（工作包见状态表K）：按已批准 K0–K6 完成 Davybase 图片批次验收、非微信图片覆盖、即时可复验 Obsidian 工作区快照、来源基线与知识资产、sealed candidate、战略影响评估、用户正式裁决、原子激活和独立复验。完成用户裁决前 `CURRENT_RELEASE` 不变。
8. **[外部材料受限；必须完成主动恢复/结案] `rnd_exp` 官方依据核验**：先搜索官方发布渠道、项目归档及可验证副本并记录来源；若穷尽后仍无原文，交付可复现的“原文不可得/当前值未核实”报告、影响范围及后续重启条件，不得宣称官方核验通过；完成该结案后继续队列。
9. **[排队—依赖验收门槛，不等用户授权] U09/O05 内部试点**（工作包见状态表R1）：公开 C 级达到 Go 且真实企业数据可用时完成真实试点；队列轮到时先完成系统/合成数据技术验证并整理授权范围。真实数据不可得则如实结案为“真实试点未验证”，不得把合成数据冒充真实证据，也不得以等待授权为由停摆。
10. **[排队—依赖证据，不等用户裁决] U10 V1.1 证据决策**（工作包见状态表R2'）：轮到后按既有标准整理已有证据并逐项给出 go/hold；证据缺口说明具体影响和替代证据路径，不把用户批准或确认设为默认下一步。
11. **[排队] 内部月度工作台与四级真实周期验收**：依赖 C 级通过、数据可用和工作台可用；完成连续3个真实月度周期、同输入人工基准、逐周期盲评和20%工时门槛。无真实周期数据时，先完成环境、流程和合成数据技术验收，形成真实验收的未满足清单及重启条件；不得以模拟数据替代真实结论。

裁决记录（2026-09-25 晚，用户四项裁决）：①分支整合归本主线串行执行；②四份「唯一」文档合并为本页唯一主线（2A）；③AI交叉评原由助手准备、用户发起，后经用户追加委托由助手安排未参与实现的隔离AI审查，结果见本页；④holdout候选由AI可复现随机抽签并归档（4A），数据冻结与oracle另行执行。

战略方向（2026-09-13，D052–D054）：企业内部月度财务经营分析工作台为最终产品，公开财报模块独立并先行成熟共享底座；顺序为 U8 → 边界重构 → 公开模块 C 级出口 → 内部工作台 → 四级验证。详见[战略重构设计](../superpowers/specs/2026-09-13-flow-strategic-reset-design.md)。

2026-09-24 补充：大麦合成发行版是“系统完整性验证工具”，知识刷新是“静态知识
维护轨”，两者可在公开 C 级外部门禁等待期间推进；二者均不改变 D052–D054 的
真实数据验收顺序，也不能代替独立 oracle、holdout 或真实企业三周期验证。

</details>

## 已完成的非待办参考

知识库增量扫描、指标库行业包、竞对五维矩阵及 O-01/O-02 地基均为已完成证据或设计输入，不再作为并行/非阻塞待办；相关详情分别见[增量扫描册](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)、[五维矩阵](../competitive/2026-09-17-five-dimension-matrix.md)和指标库规格索引。Davybase 新增图片批次及非微信覆盖属于上面第6项的未完成工作，不能据早期扫描记录判为完成。

## 纪律

2026-09-26 深链批次三验收更新（覆盖本页第 4 项旧待办措辞）：批次三本地实现及验收完成，Clean Damai verify 19/19、可见性 API 43/43、浏览器 9/9、全量 API 845 passed、生产 E2E 93/93、Web 142/142、脚本测试 101/101；M1/link 门禁通过，修复 SHA `cef0c362` 同 SHA CI 成功。全站页面状态/视口矩阵仍未完成，故第 4、5 项保持 active，不能宣布 UX 工作包关闭。细节见[深链实施计划](2026-09-26-ui-deep-link-implementation-plan.md)。

2026-09-26 CI 补记：`bc141444` CI dashboard job 的两条状态测试因 helper 将 repo-root cwd 拼成错误 fixture 路径失败；已改为按源文件目录定位，并把该 spec 加入生产 E2E。修复后本地生产 E2E 93/93 通过；修复 SHA `cef0c362` 的 GitHub Actions run `36248059559` success。

- 任务领取/勾选/提交只用本页与工作包；模块可以维护不可领取的 workstream/backlog 视图，但不得形成第二份状态真相；每完成一阶段提交推送、CI 绿才算 done；
- 详细验收步骤在工作包与归档参考规格（原统一实施计划、执行收敛计划等，均已 archived）；旧详细计划均为历史证据，不按其空复选框恢复任务；
- 工作包文件**不随状态移动**，状态由本页与 views/ 表达；
- M/P 系列、Phase/WS 历史计划只读（见 [TERMS_AND_NAMESPACES](../10_governance/TERMS_AND_NAMESPACES.md)）。
