# FLOW Phase 4 验证记录

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

验证日期：2026-09-01

功能验收提交：`a77e783dbede9afa856e117e269e89e5ad6e6c8f`

指标定义集：`flow.metrics.logistics.v1`

指标引擎：`flow.metrics.engine.v1`

## 结论

Phase 4“Metric Snapshots”完成本地与干净检出验收。FLOW 已建立独立于页面和 Excel 的受治理指标语义层：只读取 Phase 3 已发布且质量/对账合格的 canonical 版本，以严格 Decimal、维度安全 grain 和版本化目录计算 15 个物流经营与财务指标，并将精确值、公式依赖、源事实行数和完整身份原子发布为不可变 Metric Snapshot。

标准 FLOW 工作簿与结构不同的外部物流工作簿经过完整 Intake→canonical→Metric Snapshot 链路后，拥有不同的源文件和 `import_version_id`，但产生完全相同的定义哈希、值指纹和逐项精确业务值。下游 Dashboard、Investigation 与报告可以共同引用快照，不再各自计算财务数字。

## 验收门禁

| 命令或检查 | 结果 | 证据摘要 |
|---|---|---|
| `make test-metrics-known-answers` | PASS | 42 个 Phase 4 测试、1 个独立 Phase 3 Intake E2E、Ruff、mypy、迁移完整往返和机器可读摘要全部通过 |
| 干净检出完整门禁 | PASS | 在 `/private/tmp/flow-phase4-clean.if5w9u` 从提交 `7cb2686` 按锁文件安装 71 个 Python 包后完成同一门禁，无主工作区未提交文件依赖 |
| API 全量回归 | PASS | 162 个测试通过，耗时 274.49 秒；Task 9 新增 E2E 后由专项门禁另行覆盖 |
| Task 8 专项回归 | PASS | 6 个快照服务、身份、修订和故障回滚测试通过 |
| 数据库迁移 | PASS | 隔离 schema 中 `base → 0006 → base → 0006` 完整往返通过 |
| 静态检查 | PASS | Ruff 无问题；mypy 检查 67 个源码文件无问题 |
| 空 schema 自包含门禁 | PASS | 在专用 `flow_metric_gate_fix_7cb2686` schema 中由门禁自行执行 `0001 → 0006`，随后全部验收通过；验证后已删除该 schema |
| GitHub Actions | PASS | 修复提交的 FLOW CI 10 个 jobs 全部通过；`metrics-known-answers` 用时 6 分 57 秒，全量 integration 用时 7 分 44 秒；运行 [33415106672](https://github.com/davyzhong/FLOW/actions/runs/33415106672) |

## 冻结的机器摘要

```json
{
  "as_of_month": "2026-08",
  "definition_set_hash": "4214ae85339eb7495defb69f1d59fdddec5e3183d5d4ba64c966be9f53270b38",
  "definition_set_id": "flow.metrics.logistics.v1",
  "dependency_edge_count": 14,
  "engine_version": "flow.metrics.engine.v1",
  "metric_count": 15,
  "status": "PASS"
}
```

冻结答案保存在 `fixtures/expected/metric_snapshots_v1.json`，机器摘要由 `scripts/summarize_metrics.py` 输出。摘要不是独立自证：门禁会先运行目录/哈希确定性测试、计算器 oracle、持久化快照逐值比较和双工作簿端到端测试，再输出该摘要。

## 关键业务答案（T12）

| 指标 | 精确值 |
|---|---:|
| 收入 | 26,300,990.4095 |
| 毛利率 | 0.340480 |
| 经营利润 | 6,708,895.8378 |
| 经营现金流 | 4,941,609.8078 |
| 现金转换率 | 0.736576 |
| 应收余额 | 3,620,569.1952 |
| DSO | 50.245551 |

## 已证明的语义不变量

- 流量指标的组织切片合计严格等于总计，金额和数量不因维度展开而重复；
- 应收余额是半可加指标，月度、YTD 和 T12 使用各窗口最后可用期末值，不跨月求和；
- 毛利率、单均、现金转换率和 DSO 的依赖必须处于同一 grain，计算轨迹保存精确依赖值；
- 预算只生成 canonical 事实实际拥有的 Total、组织、客户群、物流产品和客户群×产品 grain，不虚构客户或区域预算；
- 标准与外部工作簿产生相同的全部指标值和指纹；
- 相同完整身份重试幂等，修订导入、目录哈希或引擎身份变化生成新快照版本；
- 已发布旧快照、值和指标依赖不可更新或删除；写入中途失败不会留下快照、定义、依赖或部分值。

## 指标发布对象

`metric_snapshot` 保存批次、导入版本、截止期间、版本、引擎、定义集、定义哈希和值指纹。发布过程先以 `building` 写入定义、依赖和值，在同一事务内切换为 `published`；故障注入证明整个写入单元回滚。

`metric_value` 同时保存：

- `value Numeric(24,4)`：页面筛选、排序和索引用；
- `exact_value`：按指标规则保留 4 或 6 位语义精度；
- `calculation_trace`：依赖指标精确值与源事实行数；
- comparison、period 与五类可选维度 ID：构成稳定、可审计的值 grain。

完整指标公式、来源、单位、维度、时间行为、比较类型、舍入与阻断码见 `docs/metrics/flow-v1-metrics.md`。

## 已知边界

- Phase 4 负责受治理指标事实，不负责 Finding 排名、驱动桥或自然语言解释；
- 当前冻结的是首个物流供应链指标集，不是全行业通用财务指标全集；
- `missing_periods` 会省略不完整比较窗口，不用估算或零值填充；
- 分母为零、依赖 grain 缺失、公式不受支持或来源资格失效时阻断快照；
- GitHub Actions 的 Node 20 弃用 annotation 来自第三方 action 元数据，作业实际在 Node 24 runner 兼容模式通过，不影响本阶段功能结论。

## CI 环境差异与修复

首次增加 `metrics-known-answers` 作业的提交 `7cb2686` 在本地和临时 worktree 通过，但远端运行 [33412230588](https://github.com/davyzhong/FLOW/actions/runs/33412230588) 失败。完整日志显示 35 个非数据库指标测试通过后，第一个数据库 fixture 因 `fact_ar_collection` 不存在而失败。

根因是新门禁隐式依赖已迁移的本地 Compose 数据卷；GitHub runner 的 PostgreSQL 是空数据库，而脚本没有在访问数据库前执行 migration。修复提交 `a77e783` 在门禁入口显式执行 `uv run alembic upgrade head`。随后在全新专用 schema 和 GitHub Actions 10 个 jobs 中复验通过。失败运行被保留为过程证据，没有重写历史。

## 下一阶段入口

Phase 5“Analysis & Findings”只能读取已发布 Metric Snapshot 和受约束 canonical-detail repository。下一阶段应建立利润/现金 Driver Model、可重现 variance bridge、Finding 候选、影响排序和证据引用；不得把分析公式重新散落到页面或 LLM prompt 中。
