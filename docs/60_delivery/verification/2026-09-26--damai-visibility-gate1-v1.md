---
doc_id: FLOW-VERIFY-DAMAI-VISIBILITY-GATE1-001
title: 大麦数据可见性 Gate 1 API 诊断证据 v1
doc_type: verification
status: draft
version: "1.0"
created_at: 2026-09-26
updated_at: 2026-09-26
owner: FLOW
commit_refs: "[3ff95115]"
evidence_refs: "[read-only-local-api-probe, stable-overlay-fingerprint, sha256-response-matrix]"
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: web-frontend
supersedes: []
superseded_by: null
---

# 大麦数据可见性 Gate 1 API 诊断证据 v1

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

完整 Gate 1 仍需完成其余缺口逐项归因和干净提交 SHA 的全目标路由复测。本记录支持已确认的故障定位与修复证据，不支持整体页面覆盖验收完成声明。

## 后续只读补充（同日；未冻结新响应哈希）

修复工作台契约后继续探测驾驶舱与指标库。此补充依赖当时本机热重载服务，未重新生成稳定 overlay 指纹，因此只作为分类线索，不能取代最终干净 SHA 复测：

- 驾驶舱12/12经营现金流趋势均返回 `trend_metric_not_published`；现金流 KPI 主值返回 `metric_grain_not_published`；4/8预算与4/8 YTD预算比较均返回 `comparison_not_published`。
- 毛利矩阵32格中，22格实际值为 `metric_grain_not_published`，24格比较值为 `comparison_not_published`。API 顶层批次、导入、质量、对账、指标快照、分析运行和新鲜度都标记为已发布/通过/新鲜，说明“流水线成功”不代表每个指标粒度与比较值已发布。
- 指标覆盖响应列出的缺失字段组：`is.interest_exp(cur)` 7个指标、`bs.short_debt(end)` 3个、`bs.long_debt(end)` 1个、`bs.ap(end)` 2个、三个 `prev_yoy` 同比基期字段3个、`cf.cash_from_sales(cur)` 1个、`cf.capex(cur)` 1个；合计18项指标。`missing` 是标准化事实层的缺失声明，尚不能单独判定原始披露、映射缺失或不适用。
- 责任初分：现金流趋势/指标粒度/比较缺失进入 Gate 3（发布快照和聚合）；18项标准化事实字段进入 Gate 2（对照合成原报表与指标公式逐项裁决适用性和事实来源）；不得直接以零填补或将财务费用等近似科目替代。
