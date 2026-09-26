---
doc_id: FLOW-VERIFY-DAMAI-VISIBILITY-GATE1-001
title: 大麦数据可见性与 Gate 4 批次历史验收证据 v2.2
doc_type: verification
status: draft
version: "2.2"
created_at: 2026-09-26
updated_at: 2026-09-26
owner: FLOW
commit_refs: "[3ff95115, 6591e148, 4932504c, 9cd43e20, 905cf544, e2417ffa, af375ba3, 101bcf23, 5510bad3, 430020f, 59b328dc, 85e907a]"
evidence_refs: "[read-only-local-api-probe, stable-overlay-fingerprint, sha256-response-matrix, damai-ocf-canonical-fixture, damai-isolated-seed-verify, damai-e2e-8-of-9, damai-e2e-9-of-9-ocf-trends-complete, margin-matrix-read-only-grain-audit, margin-comparison-selection-isolated-e2e-9-of-9, github-ci-stale-damai-coverage-assertion, secure-batch-history-api-ui-and-isolated-e2e-9-of-9, clean-sha-59b328dc-damai-e2e-9-of-9, github-dashboard-flow-test-url-conflict, dashboard-ci-url-isolation-unit-2-of-2, dashboard-playwright-7-of-7, github-run-36223558441-dashboard-success]"
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: web-frontend
supersedes: []
superseded_by: null
---

# 大麦数据可见性 Gate 1 API 诊断证据 v1

## Gate 5 CI 数据库 URL 隔离修复补记（2026-09-26）

- `scripts/test_dashboard.sh` 在 `CI=true` 时优先使用专用 `FLOW_DASHBOARD_TEST_DATABASE_URL`，默认固定到 localhost `flow_test`，不再继承通用 compose `/flow`；本地危险 URL 仍 fail-closed。
- 新增安全回归测试 2/2：CI 注入 `/flow` 被解析到 `/flow_test`；本地显式 `/flow` 在任何写操作前退出2。
- `bash scripts/test_dashboard.sh` 本机验收通过：迁移/seed 目标为 `flow_test`，摘要12个月/8卡，Playwright 7/7。常驻 `flow` 未访问或写入。
- 本轮已有其他 worktree 管理的同名 Compose 服务，因此未运行可能重配置基础设施的 `make infra-up`；直接复用健康服务。提交 `85e907a` 的 GitHub Actions run `36223558441` dashboard job 成功；workflow 的 intake/integration/data-contract 长测仍在运行，尚无总结果。旧 CI 失败记录保留为历史根因证据。

## 证据边界

- 日期：2026-09-26（Asia/Shanghai）。
- 页面/API：本机 `localhost:3000` / `localhost:8000`；只执行 HTTP GET，无写操作。
- 代码标识：Git 基线 `3ff95115`；工作树 overlay SHA-256 `1ede264890932aefc595540885a3cc34feb891f7516a137637db8bab3723529d`。同一轮完整探测前后该 overlay 指纹未变。
- 此记录固定的是诊断快照，不是干净提交版本验收。工作树含其他会话未提交变更，因此不能将基线 commit_refs 解释为响应完全由该提交单独产生，也不能据此宣称发布验收通过。
- 响应摘要哈希为原始 HTTP body 的 SHA-256；状态码单列。没有保存可能含业务内容的原始响应正文。

## 读取范围与参数

驾驶舱按月/YTD、全公司无维度筛选、`as_of=2026-08`；报表清单与 FY2025/FY2026 单份报表、四问分析工作台和经营分析概览；指标库与 `dataset=damai` 覆盖；经营分析期间清单及全部期间详情；发布快照、冻结候选、经营快照；调查发现清单与两条详情。所有请求均为只读 GET。

## API 响应矩阵

| API/请求标识 | HTTP | 原始响应 SHA-256 |
|---|---:|---|
| dashboard-month | 200 | `0d9f31119dcae24e08578dd8f0eb1472ed932e4061b0babf3020194033c1b27a` |
| dashboard-ytd | 200 | `a016544e06a273a8fbd3d45af722a504b10c6e46163a11937585c8b3f839fe94` |
| workspace | 200 | `e0c8494e3a23e9572ca6dbfda36e9ccd731f678ffa73e2cae960922066054c96` |
| statements | 200 | `0c4da8bea39e5632fb8d91d19b1814dfb5f728fef9240a84ef3f6a914c1ed54a` |
| statement-FY2025 | 200 | `6faad1f95d6baa01e4871c64bfe7bef56be193b21ce7b245fb7a228660a689da` |
| workbench-FY2025 | 500 | `e41656eb2ba6c6293bf6dd928e5a88cdbc50535cab661c1969e0f598e497ed62` |
| operations-internal-FY2025 | 200 | `9ba5660d2319b98c6040cc9d6f18be7124dc21f7c05116aa307682dd534200af` |
| statement-FY2026 | 200 | `fd822232b1c18436d693b0ef836472f6359a5a254d78a6dfb41e16185c21dc8c` |
| workbench-FY2026 | 200 | `623aee0efeababfb02f2dc447f115c1301db0dbf52384f8a51b27c0dec28fd07` |
| operations-internal-FY2026 | 200 | `1504c2bdc0c732807b375d97394e5c380f2fae01aba6c00d001437d0ced0b79e` |
| metric-library | 200 | `97fd39938070a91d422eb4c381ee5d05c7bf8610d11bffcc9caed05335c21c64` |
| metric-coverage-damai | 200 | `bc8f8707e4048b8fde3f58711c6fa07ad852170876225e0305437b97a15a56da` |
| public-periods | 200 | `fc65144184034ac650aa7a1b0b0f7e1da7e98a951c9433450da179b9a2addbe1` |
| public-CAINIAO-FY2021 | 200 | `8514fa3a232db6e585d6636376e988810104072a4f27511d6df92ec2932bbcd3` |
| public-CAINIAO-FY2022 | 200 | `770fbdbbf68284a2104f39fb2b8365984b6db9e874e41e0e9fe26a11377724a6` |
| public-CAINIAO-FY2023 | 200 | `52962b67debf26d46f67877e0afc27c7f12064c9e8055e8d8d90ac64c8f48861` |
| public-CAINIAO-Q1FY2023 | 200 | `7fb9126348419b866dbff447d774826faccaf717794059443b176a62bf805df3` |
| public-CAINIAO-Q1FY2024 | 200 | `f7d7916733db295172fd80141d9eeaf7d9164e0c72c6b5abe756131a43241bce` |
| public-DAMAI.SYN-FY2025 | 200 | `046d16dec2573a6e7732023c76ce84bb5bedc706bd2174e57fecaaca4f299bf9` |
| public-DAMAI.SYN-FY2026 | 200 | `7bcd6dbbf8583bc6b77ad4fb84e9180e8d1d62d1c2a138dc3cbec07ac5fb512f` |
| publishing | 200 | `48266fbe1eb7121553cfa92454d143ffc384672feb7abd07a69e0ffd68ddfb5c` |
| freeze-candidates | 200 | `8f297c8762fdf5c9df1c70b3a363bc132af979218888bb441a6a6918133a956b` |
| operations-snapshots | 200 | `0bcb82cfaab8cc263ddeba68af72e21d0a34c0af280661d2eb697e377773cc51` |
| investigations | 200 | `6a2aec6e29b1b14b68fd27d953352b06242f5f4a680914e034a100d8606d5e77` |
| finding-01a0d8a2-be4d-75b0-bb98-16986b018e9c | 200 | `5b16d1bb7c2b85756e6b934321d20ba334a6aeb8f7c7cbf2125f0735f536b913` |
| finding-01a0d8a2-be55-7870-b37f-2d3d9098f0fc | 200 | `4e434f8f85e203e6db88330d8c94046705289fb9aa73108bae67c1a636f92927` |

## 诊断结论

1. 服务返回 `degraded` 并非“库里完全没有数据”：大麦已有24个月经营合同数据，两份年度报表、65项指标定义以及多类发布/经营对象；问题集中在可计算覆盖、比较快照和页面入口。
2. 驾驶舱返回8张 KPI 卡、12个月趋势点（每点含4项趋势值）、8个产品、4个客群与32格毛利矩阵。经营现金流趋势12/12不可用；KPI 主值1/8不可用、预算比较4/8与YTD预算4/8不可用；矩阵实际22/32、比较24/32不可用。
3. 指标库覆盖矩阵共40项，大麦FY2025可计算22项、FY2026可计算25项；定义总数65不等于企业数据覆盖。缺项主要涉及利息费用、短期/长期借款、应付账款、销售收现、资本开支和比较期字段，须按适用性逐项裁决。
4. FY2025 四问工作台初始 GET 返回500，FY2026 返回200。根因已确认：FY2025 负债/资产比由期初 `58470903.9562 / 100909463.2794`（约58%）升至期末 `95250988.7030 / 104523501.1250`（约91%），确定性规则生成 `leverage_rising` 提示；提示对象含 `metric_code`，但严格响应模型 `ManagementWatchItem` 未声明该字段，导致 FastAPI 响应校验失败。
5. `/data` 页面初始状态没有批次历史 GET，因此已装载批次在页面上不可浏览；这是可发现性/页面入口缺口，不是事实不存在。
6. `/public` 与 `/internal` 是导航落地页，不是数据报表页；业务目标页应单独计入覆盖验收。

## Gate 1 状态

诊断范围的初始 API 读数与哈希已固定。发现上述契约缺陷后，补充回归测试先红（Pydantic 拒绝 `metric_code`），再将 `metric_code` 加入严格响应模型；工作包 API 测试 7/7、ruff、mypy 均通过，本机热重载服务对 FY2025 同一报告 GET 返回200，响应中保留 `metric_code=debt_asset_ratio`。该修复验证发生在带其他会话未提交变更的工作树中，未计入初始 overlay 哈希；待代码归属整理并提交后仍须以干净 SHA 复测。

## 毛利矩阵只读归因补充（2026-09-26）

对 canonical 文件、当前 snapshot 与只读 dashboard GET 的交叉核对显示：canonical 全期只有10种实际客群×产品组合；2026-08 `gross_margin/actual_month` 有10格、`prior_year_month` 与 `yoy_variance_month` 各8格。预算原值覆盖32格，但预算差异仅10格。热运行本机 API 返回矩阵32格、实际10格、同比8格，比较标签为“不可用”。这次读数反映当时本机运行库/代码，不绑定干净 Git SHA，因此用于定位而非验收。

归因：22个未发布实际毛利格不是快照聚合遗漏的已存在源事实；canonical 中没有相应实际组合，必须保持缺失，禁止补零。服务端比较选择逻辑要求预算或同比覆盖全部32格；两者均不满足时固定退回同比，从而丢弃较多的预算比较格。

修复与隔离验收（2026-09-26）：新增比较选择单元测试，按可用格数选单一比较类型，预算与同比覆盖数相等时预算优先；两个比较均无格时保持“不可用”。在真实隔离大麦全旅程中，新增 API E2E 断言通过：矩阵32格、实际可用10格、预算比较可用10格、标签“预算”、22格实际 `exact_value=null`；矩阵整体保持 `degraded`。完整 `bash scripts/test_damai_demo_e2e.sh`：verify 19/19、E2E 9/9；dashboard相关pytest 13 passed，ruff/mypy与前端 typecheck通过。该测试运行来自含并行会话未提交改动的工作树，不能代替本修复提交后的 CI 和干净 SHA 全目标复测；常驻数据库未写入。

CI 补充（run `36217337338`，SHA `5510bad3`）：18 个作业中仅 integration 失败，257 passed / 1 failed；唯一失败是 `test_coverage_endpoint_damai_dataset_is_synthetic_and_honest` 仍要求两个期间都必须小于40项可计算，与已批准、已生成的FY2025 37/40及FY2026 40/40发行矩阵冲突。测试已改为校验精确期间覆盖数并保持缺口结构断言；按 `services/api` 工作目录本地定向用例1/1通过。修正提交的 CI 尚待运行；不把 `5510bad3` 标作CI通过。

完整 Gate 1 仍需完成其余缺口逐项归因和干净提交 SHA 的全目标路由复测。本记录支持已确认的故障定位与修复证据，不支持整体页面覆盖验收完成声明。

## 后续只读补充（同日；未冻结新响应哈希）

修复工作台契约后继续探测驾驶舱与指标库。此补充依赖当时本机热重载服务，未重新生成稳定 overlay 指纹，因此只作为分类线索，不能取代最终干净 SHA 复测：

- 驾驶舱12/12经营现金流趋势均返回 `trend_metric_not_published`；现金流 KPI 主值返回 `metric_grain_not_published`；4/8预算与4/8 YTD预算比较均返回 `comparison_not_published`。
- 毛利矩阵32格中，22格实际值为 `metric_grain_not_published`，24格比较值为 `comparison_not_published`。API 顶层批次、导入、质量、对账、指标快照、分析运行和新鲜度都标记为已发布/通过/新鲜，说明“流水线成功”不代表每个指标粒度与比较值已发布。
- 指标覆盖响应列出的缺失字段组：`is.interest_exp(cur)` 7个指标、`bs.short_debt(end)` 3个、`bs.long_debt(end)` 1个、`bs.ap(end)` 2个、三个 `prev_yoy` 同比基期字段3个、`cf.cash_from_sales(cur)` 1个、`cf.capex(cur)` 1个；合计18项指标。`missing` 是标准化事实层的缺失声明，尚不能单独判定原始披露、映射缺失或不适用。
- 责任初分：现金流趋势/指标粒度/比较缺失进入 Gate 3（发布快照和聚合）；18项标准化事实字段进入 Gate 2（对照合成原报表与指标公式逐项裁决适用性和事实来源）；不得直接以零填补或将财务费用等近似科目替代。

## Gate 2 静态事实补齐证据（2026-09-26）

确定性财报生成器在既有24个月 synthetic 数据上新增7个规范事实：`is.interest_exp`、`bs.short_debt`、`bs.ap`、`bs.long_debt`、`cf.cash_from_sales`、`cf.capex`、`is.dep_amort`。不改变既有报表总额，生成财报从40行增至51行（IS14、BS20、CF13、权益4）。合成比例作为生成器常量及发行包附注公开。

| 工件 | SHA-256 |
|---|---|
| `fixtures/damai/statements/damai_fy2025.yaml` | `f5c3ddd4fac97dc59f18c31f11d9a74021fa5a0590f9c2ec7b93a9e8d2804322` |
| `fixtures/damai/statements/damai_fy2026.yaml` | `7ed1280aeaf18f0758f257c1059c11e37f5883683b160a6f6f6c9c3945083785` |
| `config/metrics/damai_demo_metric_coverage_v1.yaml` | `e256bc20ccf1283465ffe6e4d997de6209a335ad4ba874208ff8d85d8678f0fb` |

指标覆盖生成结果 FY2025 37/40、FY2026 40/40；FY2025未计算的三项为收入增长、净利润增长、营业利润增长，因输入包无 FY2024 比较期而标记该期间无适用比较值；FY2026三个同比值可计算。生成器重复执行后覆盖工件 SHA 不变。财报 fixture、loader、归一化测试24项通过，ruff/mypy与发行包 `--check` 通过。当前证据只证明静态工件与隔离 `flow_test` 的导入/规范化，不代表常驻 `flow` 已重载新报表；该验证仍由后续隔离发布旅程完成。

## Gate 3 月度 OCF 实际事实补齐（2026-09-26）

根因：原生成器已产出24个月 `cash_flow[].ocf`（含 E5 现金利润背离），但 canonical 财务实际转换只写入7个科目，丢弃了 OCF；指标快照依据源科目精确匹配，因此看板 OCF 实际不可用不是快照计算器漏算。修复在 canonical 转换中按月组织收入占比分摊 OCF，尾差归最后组织，保持每月集团 OCF 总额与生成器 cash flow 值完全一致。静态 `financial_actuals.jsonl` 由672行增至768行，manifest 和工作簿已重建。

验证：`tests/fixtures/test_damai_canonical.py` 25/25；`tests/fixtures/test_damai_metric_grain.py` 3/3（覆盖 actual OCF 的 total/org 两粒度与 canonical 对账）；大麦 loader + 财报 normalization 16/16；ruff、mypy、发行包 `--check`、文档 M1 与链接检查通过。源记录 SHA-256：`fixtures/damai/canonical/financial_actuals.jsonl` = `3fda66a863aa7013a782a2a79500253a99082c367b3190b7956ffbfcf55816cd`。

边界：常驻 `flow` 数据库没有被写入，现有 API/UI 仍不能据此视为已显示新 OCF。此修复须在隔离 Compose 装载后重新探测 dashboard OCF 趋势与 KPI；毛利矩阵粒度/比较缺口仍未修复。首次诊断 API 矩阵仍来自早期 dirty overlay，完整 Gate 1 干净 SHA 复测未完成。

隔离旅程已将新工作簿导入独立 `damai-demo-iso` PostgreSQL；seed 创建12个快照，`verify_damai_demo.py --check-storage` 返回19/19通过，存储工作簿读回1,327,348字节且 SHA 与单元格语义一致。随后9项浏览器 E2E 全部在页面导航阶段连接失败：日志显示验收 Next 实例启动时报 `Another next dev server is already running`，原因是此前已有同目录开发服务占用共享 `apps/web/.next/dev/lock`，因此验收实例退出。脚本已清理本次隔离 Compose 容器和卷；既有 PID 78698 未触碰。该结果不代表页面断言失败，也未证明新 OCF 在 UI 上可见；下一步先给验收进程配置专用 `distDir` 再重跑。

后续用独立 `distDir` 重跑后，seed/verify 仍19/19，浏览器8/9通过。唯一失败是 `apps/web/e2e/damai-demo.spec.ts` 的 customer-grain dashboard API 用例仍断言 OCF KPI `unavailable`，实际响应为 `available`；其余八项页面/API流程通过。该响应证明新源事实已被快照采纳。自定义 `distDir` 会令 Next 自动改写工作区 `tsconfig.json` 与 `next-env.d.ts`，临时目录删除后留下失效引用，因此不能直接在项目目录使用这一方式。修复验收应在 `work/damai-demo/` 下创建本轮专用 web 源副本（复用既有 node_modules 链接）并在那里运行 Next，清理仅作用于该副本；同时把 E2E 断言改为 OCF `available` 且 primary value 非空。毛利矩阵 grain/comparison 和完整页面覆盖仍未验收。

最终隔离 E2E 采用临时 web 源副本后通过：`scripts/test_damai_demo_e2e.sh` seed/verify 19/19，浏览器 E2E 9/9。扩展后的 dashboard API 断言确认 OCF KPI `available` 且值非空；趋势状态 `complete`，覆盖12/12，所有12个月的 OCF 趋势值均 `available` 且非空。其余八项 UI/API 与上传发布旅程通过。临时副本及 `damai-demo-iso` Compose 卷已清理；常驻 `flow` 未写入，用户现有开发服务未终止，真实 `apps/web/tsconfig.json` 未被临时副本改动。该结果关闭 OCF source/snapshot 缺口，不关闭整项工作包：毛利矩阵22/32实际值与24/32比较值缺失仍待定位，Gate1其余页面的干净 SHA 全矩阵复验也未完成。
## Gate 4 批次历史列表子项（提交 `430020f`，2026-09-26）

- 新增只读 `GET /api/v1/intake/batches`：复用 Principal 的 `INTAKE_VERSION_READ` 授权与当前企业 scope，仅查询当前 actor 创建的 `internal` 批次；按创建时间倒序最多50条，返回版本数与最新版本序号/状态。
- 新批次创建由认证 Principal 提供 `created_by`；无数据库迁移，不列出无可靠所有权的 legacy/public 批次。
- `/data` 初始页显示最近批次、批次状态、版本数、最新版本状态与创建时间；已有深链在当前账号历史中识别，不可见批次显示权限/归属提示。该列表仅为历史索引，不承诺恢复编辑会话。
- API 测试验证当前账号批次可见、另一 actor 的同企业批次不可见。隔离 Damai 全旅程在新 UI 下复跑：seed/verify 19/19、浏览器 E2E 9/9；`damai-demo-iso` 容器/卷清理完成，常驻 `flow` 未访问或写入。
- 本地验证：API+路由策略18 passed；data-workbench Vitest 16 passed；eslint、typecheck、ruff、mypy、OpenAPI 合同检查和 M1 文档门禁通过。clean SHA `59b328dc` 的隔离 Damai 全旅程 seed/verify 19/19、浏览器E2E9/9通过。
- GitHub Actions run `36222136591`（`430020f`）和 `36222489952`（`59b328dc`）的 dashboard job 均失败于同一原因：CI 注入 `DATABASE_URL` 指向本地 compose 库 `flow`，安全脚本拒绝并退出2。其余 CI jobs 尚在运行；该结果不表示批次历史 API/UI 失败，但 Gate5 CI 总体验收未通过，须按工作包记录修正变量隔离。

边界：这只补批次历史入口，未修复其他财务/经营页面的缺数或缺口展示；Gate 1 干净 SHA 全路由矩阵、Gate 3–5 其余页面与全链验收仍未关闭。
