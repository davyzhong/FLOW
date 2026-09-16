---
doc_id: FLOW-NAV-HANDOFF-001
title: FLOW 交接文档
doc_type: navigation
status: current
version: 2.1
created_at: 2026-09-11
updated_at: 2026-09-16
owner: FLOW
applies_to: handoff
---

# FLOW 交接文档（HANDOFF）

## 0. 2026-09-16（晚）最新续接：前端组件库收敛——评估 + 两项空缺落地

- **写作者**：前端组件库收敛会话（评估「行业有标准库但手写了」→ 落地空缺项）。
- **状态权威**：本节只做交接叙事；当前事实以 [PROJECT_STATE](../../00_start_here/PROJECT_STATE.md) 与 [CURRENT_ROADMAP](../../50_plans/CURRENT_ROADMAP.md) 为准。

### 背景：用户在另一项目发现「重复造轮子」问题，要求排查 FLOW

评估结论（35 个组件扫描）：底座选型规范（TanStack Query/Table、shadcn 三件套、lucide 已在）；真实空缺两处——**手写 SVG 图表约 630 行**（有意决策，与离线资料库零依赖站点同源）与 **UI 基础组件层薄**。

### 关键发现：并行会话已系统接管大头（避免撞车）

并行会话同日落地**前端 V2 提案**（`af0bfff`，2026-09-16 14:27，用户已纠正批准）：
`docs/superpowers/plans/2026-09-15-frontend-design-upgrade-proposal.md`——
Tailwind v4 + shadcn/ui + TanStack + **Recharts** 四阶段路线。阶段二第一批已进（`0dbc16a`：Button/DataTable/EmptyGuide/Provenance；`5770164` Tailwind preflight 修正）。
**Recharts 图表迁移（F-Charts）与 shadcn 组件层（S-Foundation 含 Dialog/Tabs/Toast）属其主线，本会话不触碰。**

### 本会话已完成（两项真实空缺，全部已推送）

| Commit | 内容 | 验证 |
|---|---|---|
| `a5e5a81` | **dependency-graph → @xyflow/react（reactflow v12）**：260 行手写 SVG 渲染层换库，白得缩放/平移/MiniMap/拖拽/fitView；FLOW 自有逻辑原样保留（确定性分层布局、上下游闭包高亮、tier 过滤、环兜底） | vitest 72/72、tsc 干净、eslint --max-warnings 0 干净；4 个既有用例断言强度未降 |
| `a8f3b8c` | **dashboard/icons.tsx 收敛到 lucide**：FlowIcon 保持 name API（调用方零改动），内部映射 lucide 组件 | 同上三重验证 |

### 卡住的问题 / 登记项（无硬阻塞）

1. reactflow 版图谱的**浏览器级走查未做**（e2e/statements 那套需 docker 基础设施；组件测试已过但视觉/交互需人眼或 Playwright 验收）——建议下次 `make dev-web` 后在 `/metric-library` graph tab 走查一遍。
2. 给并行会话的提示：**waterfall 瀑布图在 Recharts 无原生 series**（官方 stacked-bar 技巧模拟或保留手写）——F-Charts 批次执行时注意。
3. `@xyflow/react` 为新增依赖（+19 包）；提案 §4 的「新增依赖需用户确认」已由用户对本会话建议的「同意」覆盖。

### 下一步

1. **并行会话主线**：V2 提案阶段二剩余（F-DataTable 页面迁移/F-Provenance 溯源卡/F-EmptyGuide 空态迁移/F-ExportAudit）→ 阶段三页面模式；本会话两项已为其让路。
2. 图谱走查（上条登记项 1）。
3. 前端日常验证三连：`vitest run` + `tsc --noEmit` + `eslint --max-warnings 0`（仓库标准是零警告，非零 error）。

### 本会话踩过的坑（增量）

- **动手前先 `git log` 查并行工作**——本次靠它避免了与 V2 提案的正面撞车（我评估时看到的 ui/ 四组件与 package.json 依赖其实正是并行会话 15:19 刚铺的地基，勿把「正在分批盖的房子」误判为「烂尾」）。
- reactflow 在 jsdom 需 polyfill `ResizeObserver` + `DOMMatrixReadOnly`（官方测试指引；见 `tests/components/dependency-graph.test.tsx` 顶部）。
- eslint warnings 也要清零（`react-hooks/exhaustive-deps` 对条件初始化的 Set 会报——闭包逻辑包 `useMemo` 即解）。
- lucide 组件 props 是 `LucideProps`（继承 SVGProps），透传时做一次类型断言避免 tsc 报错。

---

## 1. 2026-09-16 续接：文档迁移 M0–M6 收官 + README v1.2

- **写作者**：文档迁移主会话（设计 V1.1 → 计划 V1.1 → M0–M6 全批次 → 用户确认关闭 → README 视觉增强）。
- **当前事实入口**：本节只做交接叙事；状态以 [PROJECT_STATE](../../00_start_here/PROJECT_STATE.md) 与 [CURRENT_ROADMAP](../../50_plans/CURRENT_ROADMAP.md) 为准（冲突时以后者为准）。

### 已完成（本迁移主线，约 35 个 commit 全部已推送）

| 批次 | 内容 | 关键提交 |
|---|---|---|
| 计划 | 设计 V1.1 修订（基线对账/存储分级/单检查器/角色映射/五题测试）+ 实施计划同步 | `05f614b`、`6733520` |
| M0 | inventory 扫描器 + 基线冻结（2740 文件 / 405 不可变锁 / 367 消费者 / path-map 2341 全处置 / 存储分级标注） | `6f3e90e`→`dd5a24b` |
| M1 | 元数据合同 + CI + 唯一入口 + D001–D051 拆分 + 三治理文档 | `0fc3488`→`a99a5b2` |
| M2 | 来源 12 组对账 + 16 知识卡 + 11 领域手册 + **发布 flow-knowledge-2026-09-12.1**（31 资产 SHA-256 锁） | `063b9ea`→`962b651` |
| M3 | 产品六件套 + 冲突矩阵 + SPEC_INDEX 15 规格 + 架构五文档（机器消费者 21 测试通过） | `970b864`、`df7f6e3` |
| M4 | CURRENT_ROADMAP 唯一路线图 + 4 工作包 + 三视图；旧计划 archived | `d9c391b` |
| M5 | 18 历史计划归档 + 顶层收口 + 生成式 DOCUMENT_STATUS + keep 化处置修订 | `99e6091`→`2f48df4` |
| M6 | links.py + `make docs-check` 六门禁 + CI m6 + **五题盲测 RUN-2 5/5** + 用户确认关闭（`e373e25`） | `e3640aa`→`e373e25` |
| README | v1.2 视觉增强（三层两模块图/四问闭环/指标生命周期/知识链图 + 2 新截图 + 数字徽章；25 截图 + 10 mermaid） | `e2812c4`→`1325cf7` |

另：同会话早期完成 ATLAS 库文件分级治理（冗余清除 736M / LFS 258M / 双 Release 861M / manifest 四态）与 4 个个人 skill 沉淀（github.com/davyzhong/zcode-skills）。

### 卡住的问题 / 登记边界（无硬阻塞）

1. **ATLAS 侧 EI 修复 T1–T3 未执行**（`ATLAS/00_治理/EI变更影响分析与改进计划_2026-08-24.md` P0 项）——当时转向存储分级，留给下一个 ATLAS 会话（约半小时机械修订）。
2. FLOW 知识维护须**用户发起**新截面（D051）；`08_wechat_sources` immutable delta 未追加；524 个微信重复候选未处置（动前必须逐文件 SHA-256 对账）。
3. 兼容入口删除条件（消费者清零 + 两个发布周期）未到期，全部保留。
4. 接续测试改进项：Q3 知识库入口未列 READING_ORDER 五件（RUN-1 在案）。
5. 最后几次 push 的远端 CI run 未逐个盯完（本地六门禁同口径全绿，风险低）。

### 下一步（按优先级）

1. **接手前先读**：CURRENT_ROADMAP、S01 工作包、`70_operations/2026-09-14-*` 协作台账——S01 及视觉统一（见下方 09-14 段）由并行会话推进中，且 09-14 段登记了 13 个未暂存文件归属待判，**先 `git status` 再动手**。
2. ATLAS：执行 T1–T3。
3. 日常变更走 `make docs-check` 六门禁后提交；新增正式文档必须合规 frontmatter（legacy-exempt 修改即失去豁免）。

### 踩过的坑（新会话必读）

**工程习惯：**
- **`cmd | tail` 掩蔽退出码**——本会话三次导致「失败状态下提交」。正确姿势：`make docs-check > log 2>&1; ec=$?`，或不用管道看完整输出。
- **shell cwd 会被 reset**（多仓库切换后回到 ATLAS）——一律绝对路径或显式 `cd` 开头。
- zsh 变量不分词（`for f in $多行` 整串一个词）→ 用 `| while read -r`；`Path.glob` 不支持 `{a,b}`。

**迁移体系（制度如此）：**
- **不可变档案旧链接不改写**（字节冻结；M5 曾误改 DECISION_LOG 被冻结测试抓回）——断链由 `link-allowlist.tsv` 解释。
- **legacy-exempt 哈希锁连锁**：改豁免文件即 must-comply；漂移多时一次性全扫批量处理，别挤牙膏。
- 新建文件先 `git add` 才被校验与引用解析（清单基于 `git ls-files`）。
- plan 终态是 `archived` 不是 `superseded`；链接改写后必须跑全库相对链接扫描（层级错误比断链隐蔽）。

**并行会话协作：**
- 动共享文件前 `stat` mtime 确认静止；对方可能重构你的工具（check_docs 被移位 + phase 机制）——**采纳新接口**；以「文件无重叠 + 独立提交」化解冲突。
- 用户未答的门槛决策不代答（CURRENT_RELEASE 等到「继续」才切）。

**外部系统（ATLAS 侧）：** GitHub Release 清洗中文文件名（label 恢复 + SHA256 notes 对账）；docx/zip 重压缩无收益；`core.hooksPath=/dev/null` 与 LFS 冲突用 `--skip-repo`。

### 快速上手

```bash
cd ~/workspace/FLOW && make docs-check        # 六门禁（约 2 分钟）
python3 scripts/documentation/knowledge_release.py --repo . --verify-current
```

---

## 2. 2026-09-14 续接：报告风视觉系统统一（GLM 协调者会话）

- **本会话交接**：[`2026-09-14-glm-coord-visual-handoff.md`](2026-09-14-glm-coord-visual-handoff.md)
- GLM 协调者会话（`mvs_ce3323c6851e4dd3961e3cfe51647d70`）收口两条主线：
  1. 把 Kimi 在 `docs/library/index.html` + 看板 Widget 的报告风视觉（hero + KPI 卡带 + 覆盖矩阵 + verdict）反哺到 apps/web 在线 `/metric-library` 和 `/statements`，顺手补 `/statements` 缺失的 `AppShell`。
  2. 把静态资料库 11 个分散 section 整合成 1 个长滚动报告，加 2480 个互链锚点 + 10 个内联 SVG 可视化（3 柱 + 4 环 + 3 折线）。
- 提交 `4be2c0f` / `e114ae3`，均已推送到 `origin/codex/s01-parallel-integration`。
- 验证：vitest 64/64、tsc 干净、eslint --max-warnings 0 干净、headless Chromium 实测 index.html 与 widget.html 零 JS 错误。
- **未做**：本会话修改了 `e2e/statements.spec.ts` 的 heading 断言，但 e2e 全套未跑（需 docker compose 基础设施）。下一会话接手后先 `git status` 判断本会话的 WIP 与其他并行会话（Kimi / Sol / route-policy / security-audit）的 13 个未暂存文件归属。

## 3. 2026-09-12 续接：O2/O3 已收口

- O2 已由 `293308c` 提交推送，CI run `34604843637` 的 16 个 job 全绿。
- O3 已完成：六主题经营快照支持 XLSX/PPTX/HTML/PDF 渲染，经营快照接入统一 `PublicationAttempt` 追加式发布登记、对象存储与报告中心下载；迁移头升至 `0024_operations_publication`。
- 正式发布的快照版本按 `(statement_report_id, report_type)` 独立递增；同一业务内容重复冻结复用同一快照，`frozen_at` 不再制造虚假新版本。生产栈已验证“冻结两次同 ID → PPTX/XLSX/HTML 发布成功 → 按 attempt 下载并校验 SHA-256”。对象存储实体缺失或内容冲突改为 typed 409，不再泄漏 500。
- O 系列当前只剩 O5，依赖内部业务事件数据授权（同 U9）。无授权时不要用公开年度数据摊月或伪造 L2/L3；可先准备脱敏数据包、字段映射与业务事件簿接入清单。U4 oracle 仍需独立会话人工录入。

---

- 写作时间：2026-09-11 凌晨
- 写作人：ZCode 会话（sess_528666d7，已完成本轮全部任务并推送）
- 读者：下一个接手的 ZCode 会话（包括我的并行会话）或 qiming 本人
- 配套阅读：`PROJECT_STATE.md` §7、`docs/superpowers/plans/2026-09-07-unified-next-plan.md`（四梯队执行顺序）、`docs/superpowers/plans/2026-09-09-operations-track-plan.md`（O 系列断点）

---

## 1. 当前任务状态总览

用户主线诉求（本轮始）：**「驾驶舱全空白很不好」→ 把阿里巴巴 + 菜鸟网络作为默认分析公司，将全部可得公开财报/经营数据导入系统**。该主线已完成；后续转入修 CI、起生产栈、修生产布局 bug。

## 2. 已完成内容（全部已提交推送，CI 绿）

### 2.1 数据资产（本轮核心产出）

| 产出 | 位置 | 说明 |
|---|---|---|
| 阿里 6 份年度业绩公告 PDF | `docs/knowledge-base/02_research/original/p5_samples/alibaba_9988/` | HKEX 官方，FY2020/21/22/24/25/26，覆盖报表 **FY2019–FY2026**；来源+SHA-256 已登记 p5_samples/README.md |
| 菜鸟招股书申请版本 PDF（666 页） | `p5_samples/cainiao_private/Cainiao_application_proof_20230926.pdf` | 2024-03 撤回、官方索引下架，经 stattimes 镜像取得；附录 I 会计师报告（PwC，IFRS，千元）含 FY2021–FY2023 完整三表 |
| 菜鸟三大报表抽取 | `scripts/p5_extract_cainiao.py` → `docs/implementation/p5/cainiao_{2021,2022,2023}fy_statements.yaml` | **42/42 勾稽绿**；条目名为翻译后中文规范名 |
| 阿里三大报表抽取 | `scripts/p5_extract_alibaba.py` → `alibaba_{2019..2026}fy_statements.yaml` ×8 | **108/108 勾稽绿**；含分年代行名适配（详见 §5 坑） |
| 菜鸟分部序列 | `docs/implementation/p5/cainiao_segment_series.yaml` | 分部收入 FY2019–FY2025、经调整 EBITA FY2023–FY2025；**FY2026 起阿里把菜鸟并入「所有其他」，单独数据止于 FY2025** |
| 菜鸟运营指标 | `docs/implementation/p5/cainiao_operating_metrics.yaml` | Selected Operating Data（包裹量/履约单量 FY21-23+两个 Q1 stub）、Non-IFRS 调整序列、FY2023 业务线占比（47.4/46.2/6.4）、网络快照（2023-06-30）；已登记为 O2/O3 输入 |
| 外部资料入库 | KB 原始档案 13 号 + synthesis 评估 + 统一计划借鉴附录 **#14** | Superset/Redash/FineBI；结论：无财务方法论增量，U8 部署参照 + 登记候选 |

### 2.2 系统内数据（已入库，可直接看）

- `statement_report` 11 份：菜鸟网络（CAINIAO，年报）FY2021–FY2023 + 阿里巴巴集团控股有限公司（9988.HK，业绩公告）FY2019–FY2026；全部已归一化（`cainiao_private`/`alibaba_9988` 映射节）→ 发布 → **客观快照冻结（objective.v1）**。
- 基础种子：会计科目 167 / 指标字典 55 / 准则 48 / 分录模板 32（与审计基线一致）。
- 驾驶舱演示批次：12 个月快照 + 分析运行（`seed_dashboard_demo.py --fresh-batch`）。

### 2.3 运行中的生产栈

- `make stack-up` 的 compose 容器：**flow-web(3000)/flow-api(8000)/flow-worker + postgres/redis/minio**，当前全部健康。
- 浏览器验证过：`/` 驾驶舱、`/statements` 报表分析（11 份真实财报）均正常渲染。

### 2.4 修过的 CI/页面 bug（提交链）

| 提交 | 内容 |
|---|---|
| `310b345` | 三外部资料入库 + 计划 #14 |
| `b09fc7d` | **阿里+菜鸟全量导入**（27 文件） |
| `849b83c` | 契约漂移修复（另一会话 O2/O3 加了 `source` 枚举没重生成 openapi） |
| `4f4dbfb` | 菜鸟运营指标抽取 |
| `17327ad` | 删除根目录 6 张微信图片（用户指令；图片原被早期提交跟踪） |
| `9de9aa2` | dashboard axe 违规修复（table-scroll 加 role/label/tabIndex）+ 基线重录 |
| `50d06b4` | **`.dashboard-loaded` 单列网格修复**（生产布局塌陷根因，见 §5.1） |

## 3. 卡住的问题 / 未决事项

1. **数据库会被并行会话的测试重置**（已发生两次）：`scripts/test_dashboard.sh`、`test_user_closure_e2e.sh` 等门禁会重灌/重置库。**重灌链（全幂等，按序执行）**：
   ```bash
   export DATABASE_URL="postgresql+psycopg://flow:flow_dev_only@127.0.0.1:5432/flow" REDIS_URL=... S3_...  # 见 services/api/tests/conftest.py
   cd services/api && uv run alembic upgrade head
   # 基础种子：import_all(session, config/metrics)（55/167/48/32）
   # 11 份 YAML：scripts/seed_statement_reports.py 逐份导入（菜鸟=年报，阿里=业绩公告）
   # 归一化+发布+冻结：normalize_report → ReviewService.publish → freeze_objective_statement_report
   # 驾驶舱：uv run python ../../scripts/seed_dashboard_demo.py --fresh-batch（在 services/api 目录跑）
   ```
2. **U4 前置 oracle 独立逐行录入**：铁律要求未参与抽取的会话人工执行，只能由 qiming 安排；本轮两批次抽取（我）与已有抽取器同源，更不能再由我代录。
3. **docker.io registry 偶发不可达**：`docker compose build web` 可能报 `node:24-alpine` 元数据拉取失败，等 20–60 秒重试即可（基础镜像本地已有）。
4. lint 存量 warning：`apps/web/components/investigation/copilot-panel.tsx` 未用变量 `context`（另一会话的代码，未动）。
5. `var/metric_library_audit.jsonl` 持续追加（测试副产品，tracked）；随任务顺手提交即可。
6. 阿里 FY2014–FY2018 更早历史、招股书商业章节更深层运营指标（仓单/干线时效等）未抽取——留作后续批次。

## 4. 下一步计划（按优先级）

1. **O2/O3 收尾（并行会话车道，进行中）**：经营轨季度级接线 + 渲染剩余（pdf/freeze wiring）；数据输入已备好（`cainiao_segment_series.yaml` + `cainiao_operating_metrics.yaml`，已在 O 计划登记）。完成后做「数据→六主题→页面」端到端验收。
2. **经营驾驶舱接真实数据**：O2 接通后，把驾驶舱月度演示批次替换/并列真实季度序列。红线：不得把年度公开数据摊月。
3. **抽取批次扩展（可选）**：阿里 FY2014–2019 历史公告；招股书商业章节深层运营指标。
4. **U9/U10**（第四梯队）：内部数据试点（等授权）、证据决策包（已就绪）。
5. **U4 oracle**（用户安排独立会话）。
6. 长期：6.1 JDL 唯一键已由 group_ordinal 方案关闭；7 rnd_exp 临时挂 4301 待《应用指南汇编 2024》原文核对。

## 5. 踩过的坑（重点，后续必读）

### 5.1 生产 vs 开发的样式门禁缺口（本轮最大坑）
- e2e 视觉基线跑在 `next dev` 上；**生产容器（standalone build）渲染从未被门禁覆盖**。AppShell 重构后 `.dashboard-loaded` 残留 `188px 侧栏+内容` 旧网格 → 生产页工作区塌成 188px 宽、文字全部重叠，而 dev/e2e 一路绿灯。
- **更深的坑**：重录基线会把当时的（坏）布局固化成新基线——重录前必须先用浏览器肉眼/量 DOM 验证布局正确。
- 修完后验证生产：起容器→playwright 量 `.metric-grid` 宽度（正常 ~950px）→截图。

### 5.2 Playwright 快照路径随 cwd 变化
- 从仓库根跑（门禁脚本方式）→ 读 `apps/web/e2e/__snapshots__/`；从 `apps/web` 跑 → 读 `e2e/dashboard-visual.spec.ts-snapshots/`。**重录必须用 `PLAYWRIGHT_UPDATE_SNAPSHOTS=1 bash scripts/test_dashboard.sh`（根目录）**。
- linux 基线 = darwin 基线字节级复制（捆绑字体渲染确定，历史惯例 cfa7090）。

### 5.3 公告 PDF 抽取陷阱（写新抽取器前必读）
- **行名锚定必须「行首」**：`資產總額` 会命中 `流動資產總額` 子串；在去空格串上 find + pos_map 映射回原文验证行首。
- **脚注标记 vs 负数**：`(1)` 是脚注、`(569)` 是负数——脚注正则只允许单数字 `^\(\d\)$`，且只在未收集到数值时跳过。
- 注号会插在行名中间（`...consolidated 33, limited partnerships 37(b)`）：匹配键截到注号前，注号 token 允许尾逗号。
- 百分比列（`4%`）、「不適用」占位都要当数值占位收集，按列位取数。
- **行名随年代漂移**：無形資產攤銷「和/及/无減值」三变体；其他淨收益/其他淨收支/其他淨（損失）收益；FY2025-26 把「其他淨（損失）收益」（经营内）与「其他淨收支」（经营下）拆成两行，勾稽链要按年代取数；菜鳥物流服務→菜鳥→菜鳥集團。
- 年度列固定取 6 列中的第 4、5 个（Q/Q/USD/FY/FY/USD）；财状表 3 列取第 1、2；分部表旧 6 列（百分比穿插）新 4 列。
- 纯数字小计行与带标签小计行（`Total assets ...`）混排，识别要用「纯数字行 or 已知 Total 标签」白名单，不能剥任意行标。

### 5.4 导入与归一化
- `report_kind` 枚举受限：`['一季报','三季报','业绩公告','中报','年报']`——公告用「业绩公告」，招股书会计师报告用「年报」。
- 身份键 `(company_name, stock_code, report_kind, period_label)`；内容哈希相同幂等重建，不同则递增 version（重述保留）。
- 归一化公司键在 `normalization.py` 的 `COMPANY_KEY_BY_STOCK`（CAINIAO→cainiao_private，9988.HK→alibaba_9988）。
- 别名映射 `{item: is.x, abs: true}` 做符号转换；未映射行 item_id=None 如实保留（不猜测）。
- 冻结前置：`status=published` + source_ref + source_sha256 + 归一化行存在。

### 5.5 知识库 manifest 重建
- 旧 mtime/顺序必须从 **git HEAD** 恢复（`git show HEAD:...`，**cwd 必须是仓库根**，否则静默全刷——已踩过）；逐文件 size+sha256 对比，未变保留旧 mtime。
- mime：`.gz`→`application/gzip`；sha256sums 格式 `hash  ./path`（两空格带 `./`）。

### 5.6 运行环境
- 起 compose 栈前杀掉残留 `next dev`/`uvicorn`（并行会话遗留进程占 3000 端口会导致 web 容器绑定失败）。
- `make stack-up` 用 `--build`；单独重启 web 若代码变了要 `docker compose build web` 再 `up -d web`。
- 驾驶舱 API 404（dashboard_not_ready）= 库里没有已发布批次，先跑 `seed_dashboard_demo.py --fresh-batch`。
- pytest 在 `services/api` 目录内跑；门禁脚本自带起停服务，跑前 `pkill -f "next dev"; pkill -f uvicorn`。

### 5.7 协作纪律
- **另一个会话也是我**（qiming 同时开多个 ZCode 会话）：写文件前 `git status`/`git fetch` 查并发；发现工作区有不认识的改动（如别名映射被改写）→ 那是在途工作，**不要卷进自己的提交**；推送被拒走 fetch/rebase。
- CI 红先分清是谁的提交引入（`gh run list` 对照提交史），别盲目替活跃会话修它的 WIP。

## 6. 关键命令速查

```bash
# 起生产栈（常驻）
make stack-up                      # web:3000 api:8000
# 重灌数据（库被测试重置后）
# …见 §3.1 重灌链
# 跑三个曾经红过的门禁
bash scripts/test_dashboard.sh
bash scripts/test_investigation_e2e.sh
FLOW_USER_CLOSURE_ONLY=1 bash scripts/test_user_closure_e2e.sh
# 重录视觉基线（根目录！）
PLAYWRIGHT_UPDATE_SNAPSHOTS=1 bash scripts/test_dashboard.sh
# CI 状态
gh run list --limit 3
```
