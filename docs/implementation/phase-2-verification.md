# FLOW Phase 2 验证记录

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

验证日期：2026-08-30

验证实现提交：`32ec9be20bf4365e20d2475132d41cdc08098767`

数据契约版本：`flow.excel.v1`

## 结论

Phase 2“标准 Excel 数据契约与高拟真 fixture”验收通过。FLOW 已拥有可执行、可版本化的数据中间层入口：同一份机器可读 YAML 契约驱动标准 Excel、解析校验、确定性 fixture、PostgreSQL 持久化和再次导出。下游指标、驾驶舱、AI 与报告无需也不得直接依赖外部 Excel 的列位置或显示名称。

## 验收门禁

| 命令或检查 | 结果 | 证据摘要 |
|---|---|---|
| `make test-data-contract` | PASS | 34 个数据契约/fixture 测试、3 个数据库集成测试、Ruff、mypy 和业务摘要全部通过 |
| `make phase-1-acceptance` | PASS | 干净 worktree 中 67 个 API 测试、2 个 Web 测试、20 个集成测试、迁移往返、合约和六服务 smoke 全部通过 |
| 工作簿重新生成 | PASS | 相同输入产生稳定的标准工作簿和 canonical fixture |
| Excel 解析 | PASS | 解析依赖第 2 行稳定 `field_id`，移动列或修改显示名称不改变语义 |
| PostgreSQL 往返 | PASS | Excel → canonical package → PostgreSQL → canonical package → Excel 的语义快照零差异 |
| 工作簿视觉检查 | PASS | 10 张工作表均可打开和渲染；填写说明页已调整列宽与自动换行，标题、字段 ID、类型提示和数据区可读 |

## 已冻结的数据契约

标准工作簿包含 10 张有固定身份和顺序的工作表：

1. `00_填写说明`
2. `01_分析批次`
3. `02_经营实际`
4. `03_财务实际`
5. `04_月度预算`
6. `05_应收回款`
7. `06_客户主数据`
8. `07_物流产品`
9. `08_组织与区域`
10. `09_管理科目`

每个数据页第 1 行是可修改的中文显示名，第 2 行是不可变 `field_id`，第 3 行是类型和单位提示，第 4 行起为数据。解析器按照 `field_id` 而不是列号或显示名称建立语义身份。

契约能识别并返回有类型的错误，包括：缺失、重复或未知字段 ID，错误契约版本，断裂外键，重复事实粒度，以及把文本 `NULL` 填入数值字段。空值、空字符串、零和文本 `NULL` 不被视为同一个值。

## 基准数据集

fixture 使用确定性规则生成，不含随机因子：

- 分析窗口：2025-09 至 2026-08，共 12 个月；
- 同比窗口：2024-09 至 2025-08，共 12 个月；
- 2 个客户群、16 个客户、8 个物流产品、3 个组织、4 个区域、9 个管理科目和 2 个场景；
- 经营实际 3,072 行；
- 财务实际 432 行；
- 月度预算 120 行；
- 应收回款 1,920 行；
- 加载数据库时形成 5,592 条行级血缘记录。

冻结的主要已知答案：

| 指标 | 精确值 |
|---|---:|
| 分析期收入 | 26,300,990.4095 |
| 毛利率 | 0.340480 |
| 经营利润 | 6,708,895.8378 |
| 经营现金流 | 4,941,609.8078 |
| 现金转换率 | 0.736576 |
| 最终季度经营利润预算差额 | -651,579.5664 |
| 最终月逾期应收 | 1,293,530.5934 |
| 经营与财务收入对账差异 | 0.0000 |
| 经营与财务直接成本对账差异 | 0.0000 |

数据故事同时以机器可复核断言冻结：收入同比增长，重点客户量下降而国内营销客户增长，末季毛利率恶化、单票运输成本上升，现金转换率低于 1，逾期应收集中，且末季经营利润未达预算。

## 远端 CI

实现提交 GitHub Actions run：<https://github.com/davyzhong/FLOW/actions/runs/33303891544>

| Job | 结果 |
|---|---|
| `static-python` | PASS |
| `static-web` | PASS |
| `unit` | PASS |
| `integration` | PASS |
| `contracts` | PASS |
| `migrations` | PASS |
| `smoke` | PASS |
| `data-contract` | PASS |

## 主要交付物

- 机器可读契约：`templates/excel/flow_v1_contract.yaml`；
- 人类可读说明：`docs/data-contract/flow-v1.md`；
- 标准模板及参考数据：`fixtures/workbooks/flow_standard_v1.xlsx`；
- canonical JSONL 和清单：`fixtures/canonical/`；
- 冻结业务答案：`fixtures/expected/known_answers.json`；
- 契约、记录、解析、语义比较、持久化和导出实现：`services/api/src/flow_api/data_contract/`；
- 一键验收入口：`make test-data-contract`。

## 边界与下一阶段

Phase 2 只接受符合 `flow.excel.v1` 的标准工作簿。它刻意不包含非标准 Excel 的表头/数据区域识别、别名匹配、AI 字段映射、清洗审计、质量问题确认和批次原子发布；这些属于 Phase 3“Intake、Mapping & Quality”。

Phase 3 必须以本阶段冻结的契约、fixture 和已知答案作为验收基线：标准工作簿和一份故意扰动的非标准工作簿最终应产生相同 canonical 总额，并保留完整版本、质量、映射与字段级血缘。
