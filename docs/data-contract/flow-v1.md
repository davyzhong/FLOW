# FLOW 标准 Excel 数据契约 V1

## 1. 定位与边界

`flow.excel.v1` 是 FLOW V1 的第一版可执行数据契约，也是标准数据中间层的外部交换格式。它解决两个入口问题：

1. 业务、财务或外部协作人员可以直接填写标准工作簿；
2. ERP、业务系统和非标准 Excel 可以先转换成同一结构，再由用户核对。

标准 Excel 不是系统数据库。只有接入与映射模块可以读取工作簿；指标、驾驶舱、Investigation、AI 和报告发布必须读取 PostgreSQL 标准表或不可变快照，不能绕过数据中间层直接依赖原始 Excel。

本契约在 Phase 2 只接受结构有效的 FLOW 标准工作簿。非标准表识别、字段别名、AI 映射、清洗审计、警告确认、失败重试和正式批次发布属于 Phase 3。

## 2. 版本、期间与情景

- 契约版本：`flow.excel.v1`；
- 参考批次：`FLOW_REFERENCE_2026_08`；
- 主分析窗口：2025-09 至 2026-08，共 12 个月；
- 同比窗口：2024-09 至 2025-08，共 12 个严格匹配月份；
- 实际情景：`ACTUAL`；
- 预算情景：`BUDGET_FY26_V1`；
- 本位币：CNY；
- 金额与数量：数据库使用 `NUMERIC`，Python 使用 `Decimal`，工作簿使用带明确格式的数值单元格。

主产品体验仍是 12 个月经营分析。额外的 12 个同比期间是为了让后续同比从标准事实层计算，而不是把同比百分比硬编码到页面。

## 3. 通用工作表约定

所有工作表采用同一三行表头：

- 第 1 行：可读的中文显示名称；
- 第 2 行：不可随意修改的稳定字段 ID；
- 第 3 行：类型、单位、必填和空值提示；
- 第 4 行起：数据。

解析器只依赖第 2 行稳定字段 ID，不依赖列位置或中文显示名称。用户可以移动列或调整第 1 行显示名称，但不能删除、重复或发明字段 ID。记录关联使用稳定业务编码，不使用 Excel 行号。

## 4. 十张核心工作表

| 顺序 | 工作表 | sheet_id | 业务作用 | 标准粒度 |
|---:|---|---|---|---|
| 00 | `00_填写说明` | `instructions` | 填写路径、字段规则、错误级别和对账说明 | `section_code` |
| 01 | `01_分析批次` | `analysis_batch` | 契约版本、分析期、同比期、币种和情景 | `batch_code` |
| 02 | `02_经营实际` | `operating_actual` | 订单、履约件量、收入和三类直接成本 | `month_key` + `organization_code` + `customer_code` + `logistics_product_code` + `region_code` |
| 03 | `03_财务实际` | `financial_actual` | 组织、月份和管理科目上的财务实际 | `month_key` + `organization_code` + `management_account_code` |
| 04 | `04_月度预算` | `monthly_budget` | 指标预算及可选客户板块、产品、科目切片 | `month_key` + `organization_code` + `customer_segment_code` + `logistics_product_code` + `management_account_code` + `scenario_code` + `metric_code` |
| 05 | `05_应收回款` | `ar_collection` | 应收余额、到期、逾期、回款和账龄 | `month_key` + `customer_code` + `invoice_number` + `aging_bucket` |
| 06 | `06_客户主数据` | `customer_master` | 客户、板块、行业、等级和信用账期 | `customer_code` |
| 07 | `07_物流产品` | `logistics_product` | 八类物流产品及可选父级 | `logistics_product_code` |
| 08 | `08_组织与区域` | `organization_region` | 在同一外部表维护组织树和区域树 | `entity_type` + `entity_code` |
| 09 | `09_管理科目` | `management_account` | 管理科目、类别和财务科目映射 | `management_account_code` |

YAML 是字段定义的唯一机器可读来源：[`templates/excel/flow_v1_contract.yaml`](../../templates/excel/flow_v1_contract.yaml)。每个字段都声明 `field_id`、显示名称、类型、必填、可空、说明，以及适用的单位、精度、枚举、最小值、格式和外键。

## 5. 字段类型、单位与空值

支持六种类型：`string`、`integer`、`decimal`、`month`、`datetime`、`enum`。

- `month` 使用 `YYYY-MM`；
- `datetime` 使用带时区 ISO 8601；
- 金额单位为 CNY，数量字段明确标识 order、shipment 或 day；
- `decimal` 按字段声明的 scale 保存，V1 事实值为四位小数；
- `enum` 只能使用契约中列出的值；
- 必填字段不能同时声明为可空；
- 只有真正空白的可选单元格表示 null；
- 空字符串、数字 0、缺失值和文本 `NULL` 含义不同，解析器不会自动混用；
- 可选预算维度保持 null，不能用空字符串或虚构的 `ALL` 编码代替。

## 6. 主外键与稳定身份

主要关系如下：

- 经营实际的组织、客户、物流产品和区域必须存在于主数据；
- 财务实际的组织和管理科目必须存在于主数据；
- 月度预算的组织、情景及非空可选维度必须存在；
- 应收回款的客户必须存在；
- 客户的板块编码在客户主数据中形成两类稳定板块；
- 产品、组织、区域和管理科目的父级编码必须指向同类稳定业务编码。

外部工作簿使用业务编码。导入 PostgreSQL 时，系统以固定命名空间生成确定性 UUID，并保留每条事实的 `import_version_id` 和 `source_record_id`。当前参考批次为每个工作簿数据行创建一条行级血缘记录，可定位工作表和行；Phase 3 将进一步记录字段级转换事件。

## 7. 经营财务对账

参考数据执行两项零容差基准对账：

1. `02_经营实际.revenue` 合计等于 `03_财务实际.REVENUE`；
2. 经营实际三类直接成本之和等于财务实际 `WAREHOUSING_COST`、`TRANSPORTATION_COST` 和 `OTHER_DIRECT_COST` 之和。

当前参考批次两项差异均为 `0.0000`。Phase 3 会把允许阈值、阻断状态、用户确认和修订版本纳入正式质量工作流。

## 8. 错误分类

### 阻断错误

- 缺少必需工作表或字段 ID；
- 字段 ID 重复、未知或契约版本不兼容；
- 必填数据缺失或数据类型/精度错误；
- 稳定粒度重复；
- 主外键关系断裂；
- 经营财务对账超出配置阈值。

### 确认警告

- 异常负值；
- 零订单但有收入；
- 单位或数量级疑似错误；
- 毛利率、回款率或账龄结构超出业务阈值。

Phase 2 解析器实现结构与关系阻断。确认警告、操作者、原因和确认事件将在 Phase 3 实现。

## 9. 参考 fixture 与已知答案

参考数据不是随机数。它由月份、客户板块、客户、产品、区域、季节性和末季运输成本冲击等显式驱动因素生成。

| 对象 | 行数 |
|---|---:|
| 期间 | 24 |
| 客户板块 | 2 |
| 客户 | 16 |
| 物流产品 | 8 |
| 组织 | 3 |
| 区域 | 4 |
| 管理科目 | 9 |
| 经营实际 | 3,072 |
| 财务实际 | 432 |
| 月度预算 | 120 |
| 应收回款/账龄 | 1,920 |

已知故事包括：收入同比增长、大客户订单下降、国内营销客户增长、末季毛利率下降、单位运输成本上升、现金转换低于 1、应收风险集中、增长产品毛利低于预算以及末季经营利润不达预算。精确答案保存在 [`fixtures/expected/known_answers.json`](../../fixtures/expected/known_answers.json)。

## 10. 生成、验证与导入导出

重新生成标准数据和工作簿：

```bash
cd services/api
uv run python ../../scripts/generate_phase_2_fixtures.py
uv run python ../../scripts/generate_standard_workbook.py
```

执行 Phase 2 完整门禁：

```bash
make test-data-contract
```

门禁会验证 YAML、fixture、已知答案和已提交工作簿可重建，运行类型/静态检查，并执行：

```text
标准包 → Excel → 标准包 → PostgreSQL → 标准包 → Excel → 标准包
```

比较覆盖行数、稳定业务键、记录 ID、Decimal 精度、空值、关系、合计和经营财务对账。所有边界必须零语义差异。

## 11. 兼容策略

- 同一版本内可以调整显示名称、说明、列顺序和不改变语义的样式；
- 字段 ID、类型、粒度、空值含义或业务定义的破坏性变化必须发布新契约版本；
- 已导入批次保留原契约版本和源文件哈希，不能被新模板静默重写；
- 下游只依赖标准表和版本化快照，因此数据源变化不会直接破坏指标、页面和报告。
