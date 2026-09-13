---
doc_id: FLOW-SPEC-FINANCIAL-FACTS-V2
title: 统一财务事实契约 V2（Financial Facts Contract V2）
doc_type: specification
status: review
version: 2.0
created_at: 2026-09-13
updated_at: 2026-09-13
owner: FLOW
decision_refs: [D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
applies_to: services/api, docs/superpowers/specs/financial-facts-contract.md
---

# 统一财务事实契约 V2（Financial Facts Contract V2）

- 依据：战略重构设计 V1.1 §5.3（企业内部分析工作台对事实合同的扩展要求）、§12 失败与降级；S01 计划 Task 3 / Task 4 / Task 5。
- 上位合同：V1 合同 `docs/superpowers/specs/financial-facts-contract.md` 永久原位、机器消费，本规格是其**向后兼容扩展**，不重述其全部规则而是全部继承。
- 目标：让同一份规范事实对象既能表达公开披露事实，也能表达企业内部月报事实（实际/预算/预测、企业空间、月度周期、Excel 来源定位）。

## 1. 输入

- V1 合同全部字段与规则（subject、original_label、period、semantics、unit、scope、standard、数值 Decimal 禁 float、None≠0、缺失传染等）；
- 企业内部输入包：财务报表或科目余额、实际与预算、上年同期与上月、应收/回款/现金（战略设计 §5.3 最低常见输入）；
- 导入上下文：企业空间、月度分析周期、映射版本、管理口径版本、源文件内容。

## 2. 输出

- V2 纯领域模型（不依赖 ORM/HTTP）及其合法组合校验；
- V1→V2 无损适配器与 canonical 显式适配（Task 4）；
- 数据库迁移 0025：V2 列与合法组合 CHECK；
- 企业空间（enterprise）与月度分析周期（analysis_cycle）对象（Task 5）。

## 3. 对象

V2 在 V1 字段之上**新增**以下最小字段（全部可空仅在 §4 合法组合允许时）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `scenario` | `actual / budget / forecast` | 情景身份；与 V1 事实区分的关键维度 |
| `scenario_version` | 字符串 | 同一情景的版本（如预算 V1/V2），预算版本身份的载体 |
| `enterprise_id` | 标识符 | 企业空间；公开事实为空 |
| `analysis_cycle_id` | 标识符 | 月度分析周期；内部事实必填 |
| `org_scope` | 组织/管理范围 | 企业内组织范围；不同于 V1 `scope`（合并范围），两者并存 |
| `source_file_sha256` | 64 位十六进制 | 源文件内容哈希 |
| `source_locator` | `WorkbookLocator{workbook, sheet, cell_or_range}` | Excel 工作簿/工作表/单元格或区间定位；与 V1 公开定位（page/table/row）互补 |
| `import_version` | 字符串 | 导入管道版本 |
| `mapping_version` | 字符串 | 字段映射版本 |
| `management_basis_version` | 字符串 | 管理口径版本 |
| `comparison_period_id` | 标识符 | 同比/环比比较期间身份；比较事实必须同时携带两个完整 V2 身份（本期 + 比较期） |

## 4. 状态与合法组合

事实的合同形态由 `(profile, contract_version, cycle)` 三元组决定，仅以下组合合法，其余由单一数据库 CHECK 与领域校验双重拒绝：

| profile | contract_version | analysis_cycle_id | 含义 |
|---|---|---|---|
| `legacy` | 1 | NULL | 迁移前存量 V1 事实 |
| `public` | 1 或 2 | NULL | 公开财报事实（V2 允许携带 source_file_sha256 等扩展） |
| `internal` | 2 | NOT NULL | 企业内部月度事实 |

- `legacy` 事实只可被读取与适配为 V2，不可新增写入；
- `internal` 事实必须携带 enterprise_id、scenario、scenario_version、import/mapping/management-basis 三个版本与 source_file_sha256 + source_locator。

## 5. 不变量

1. V1 全部不变量原样继承：数值用 Decimal 禁 float；None≠0；缺失如实表达且沿计算链传染；不同 scope/standard 不隐式合并或换算；original_label 不被标准映射覆盖；
2. V1→V2 适配**无损**（public profile 保留 page/table/row 定位）；**禁止**有损的 V2→V1 反向适配——需要 V1 视图时只能投影并显式丢弃扩展字段，且投影结果不得回流为事实；
3. 同比/环比必须引用两个完整 V2 身份，不允许只用期间标签拼接；
4. 同一 (enterprise, cycle, scenario, scenario_version, 科目/指标, period) 唯一确定一条事实；重复导入产生新 import_version 而非覆盖；
5. 已冻结周期内的事实不可改写（与发布冻结合同一致）。

## 6. 失败行为

| 情况 | 必须行为 |
|---|---|
| 非法 profile/version/cycle 组合 | 写入前领域校验拒绝 + 数据库 CHECK 拒绝（双重） |
| 映射不确定或来源缺失 | 阻止受影响事实入库，生成精确补充请求；可证明部分继续 |
| 对账不闭合 | 显式显示差异与影响；受影响事实不得进入发布 |
| V2→V1 有损适配尝试 | 直接报错，不允许静默丢字段 |
| 比较期间身份不完整 | 该比较计算失败并说明缺哪一侧身份 |

## 7. 迁移

- 迁移 0025：新增 V2 列（全部可空以容纳 legacy/public）+ 合法组合 CHECK + enterprise/analysis_cycle 表（Task 5 细化）；
- 存量 V1 事实标记 `profile=legacy, contract_version=1`，原地保留；
- 公开入口后续按 Task 4 适配器写入 `profile=public`；内部工作台启用后写入 `profile=internal`；
- 回滚策略：0025 只加列与约束，回滚为删除新增列，存量 V1 数据不受影响。

## 8. 验收

1. V2 纯领域模型单测覆盖：合法/非法组合、Decimal 精度、None≠0、缺失传染（继承 V1 契约测试口径）；
2. 适配器测试：V1→V2 往返无损（public 定位字段全保留）；V2→V1 投影显式声明丢弃字段且不得回写；
3. 迁移 0025 升级/回滚测试通过，单一 CHECK 覆盖全部非法组合；
4. 企业空间与月度周期可创建、可隔离（跨企业读取被拒绝由 RBAC 规格承接）；
5. 既有公开财报事实、冻结快照与来源定位在迁移后逐字节一致（对 U8 冻结基线可重放）；
6. 本规格转 approved 后，Task 3/4/5 实现与本规格逐条对账，偏差回本规格修订。
