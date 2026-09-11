# FLOW 交接文档（HANDOFF）

## 0. 2026-09-12 最新续接：O2/O3 已收口

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
