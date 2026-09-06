# 统一财务事实契约（Financial Facts Contract）

- 版本：v1（A02，2026-09-06）；状态：有效，进入实现门禁
- 依据：[客观财务分析产品方向](2026-09-06-objective-financial-analysis-direction.md) 第 3 节五条链第 1 条（数据）与第 2 条（口径）
- 适用范围：公开财报抽取入口与企业内部数据适配入口共用；两个入口的事实一旦进入系统，必须满足本契约才能被指标、分析、复核与发布消费
- 参考实现：`services/api/src/flow_api/statements/fact_contract.py`；契约测试：`services/api/tests/statements/test_fact_contract.py`

## 1. 事实的组成

一条财务事实（FinancialFact）= 一个确定主体在某个确定期间/时点、某个确定口径下的一个数值（或一次如实缺失），并携带完整来源。字段：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `subject` | 主体（公司名 + 证券代码/内部主体 ID） | 必填 |
| `original_label` | 披露原文行名 | 必填；标准项目映射另存（B03），不覆盖原文 |
| `period` | `Period{start, end, kind, label}` | `kind ∈ single_month / single_quarter / ytd / annual / point` |
| `semantics` | `flow`（期间流量）/ `stock`（时点余额） | 与 period.kind 一致性见 §2 |
| `unit` | `Unit{currency, scale}` | currency 用 ISO 代码；`scale ∈ 1 / 1e3 / 1e6`，缩放规则见 §4 |
| `scope` | `consolidated / parent / segment / other` | 合并范围；不同 scope 的事实不得合并（§5） |
| `standard` | `CAS / IFRS / US_GAAP` + 可选版本与有效期间 | 准则差异不做隐式换算 |
| `source` | `SourceLocator{file_sha256, page?, table?, row?}` | 文件哈希必填；页/表/行至少一项必填（等效定位） |
| `value` | `Decimal | None` | 禁止 float；`None` 必须携带 `missing_reason`（§3） |
| `missing_reason` | `not_disclosed / not_applicable / parse_unresolved / redacted` | `value` 非空时本字段必须为空 |
| `restated` | bool | 重述版本与原版并存，查询必须显式选择版本 |
| `caliber_note` | 口径附注（如「期末口径，未年化」） | 可选 |

## 2. 期间与时间语义

- `flow` 事实必须有真实期间跨度（`start < end`）；`stock` 事实必须是单一日期（`start == end`）。
- `kind` 与跨度一致性：`single_quarter` ≈ 一个自然季；`annual` = 完整财年；`ytd` 起点必须是财年首日；`point` 仅与 `stock` 搭配。
- **单季/累计不可误混**：`single_quarter` 与 `ytd`/`annual` 的事实不可直接比较或相减；允许的同源转换只有「同 `kind` 的 flow 相加」（如四个 `single_quarter` 加总为 `annual`，且主体/口径完全一致）。
- `stock` 事实跨期间**不可相加**（时点余额之和没有财务含义）。

## 3. 空值语义（空值不等于零）

- `value = None` 是「未知/未披露」，不是 0。任何把 `None` 当 0 参与的计算都是契约违规。
- `missing_reason` 必须区分：`not_disclosed`（报表未披露该行）、`not_applicable`（该主体不适用）、`parse_unresolved`（解析未定位）、`redacted`（脱敏移除）。
- 汇总时 `None` 的处理：任一输入为 `None` 则结果为 `None`（缺失传染），不得静默按 0 加总；是否允许「披露明确为零」以 `value = 0` 表达（与缺失严格区分）。

## 4. 单位与缩放

- `scale` 只允许 10 的幂（1/1e3/1e6），保证 Decimal 下缩放**可逆**且精确：`to_base(to_base(v, a→b), b→a) == v`。
- 不同 `currency` 的事实不得合并或比较；本契约不做汇率换算（汇率属于分析层显式输入）。
- 展示层的「亿元/万元」格式化必须可逆回 `unit` 原始值，展示值不得进入计算。

## 5. 合并范围、准则与冲突拒绝

- `scope`、`standard`、`currency`、`semantics` 任一不同的事实**拒绝合并**（抛出冲突错误，不降级、不猜测）。
- 重述（`restated=true`）与原版并存；默认查询取最新版本但旧版可访问；报告使用哪个版本必须显式记录。
- 同一 `(subject, original_label, period, scope, standard)` 下出现两个不同 `value` 且非重述关系时，视为冲突，拒绝入库。

## 6. 精度和符号

- 所有金额以 `Decimal` 携带；序列化跨 JSON 用精确字符串（沿用 `as_exact_string`）。
- 符号以披露原文为准：括号负数、负号、绝对值列必须归一为带符号 Decimal 并留痕转换规则；`abs` 归一只允许在抽取层按映射表执行（如腾讯括号负数），不允许在分析层隐式取绝对值。

## 7. 契约违规清单（门禁判定）

以下任一情况为违规，测试与运行时均拒绝：

1. `flow` 事实无跨度或 `stock` 事实有跨度；
2. `value=None` 且无 `missing_reason`，或 `value` 非空却带 `missing_reason`；
3. 不同 scope/currency/standard/semantics 的事实合并；
4. 单季与累计直接比较/相减；`stock` 跨期相加；
5. 非 10 幂缩放因子，或缩放后不可逆；
6. 来源缺文件哈希，或页/表/行三项定位全缺；
7. 以 float 携带金额。
