# FLOW Phase 3 验证记录

> **适用性说明（2026-09-04，代码基线 `c1a59d1`）**：本文结果属于所列日期/阶段的验收快照，保留当时测试数量、环境和结论；不代表对当前提交重新执行全量测试或完成生产验收。 人工覆盖映射的恢复及前端警告确认属于后续补修，不由本阶段自动映射门禁单独证明。
> 当前入口见[文档导航](../README.md)，后续缺陷修复与验证边界见[2026-09-04 修复验收](../implementation/2026-09-04-review-repairs.md)。

验证日期：2026-08-31

验证实现提交：`4671fb269cdeedfe559cd3dec795f16fffd77b47`

数据契约版本：`flow.excel.v1`

## 结论

Phase 3“Intake、Mapping & Quality”完成本地、干净检出和远端持续集成验收。FLOW 的数据中间层入口已经从“只解析标准模板”升级为可审计的导入边界：标准 FLOW 工作簿与刻意扰动的外部物流工作簿通过同一套识别、映射、转换、质量、对账和发布流程，产生相同的 canonical 业务语义；源文件、原始值、转换规则、字段级血缘、确认记录和历史版本均保留。

## 验收门禁

| 命令或检查 | 结果 | 证据摘要 |
|---|---|---|
| `make test-intake-e2e` | PASS | 41 个 intake 测试、2 个真实 API 测试、10 个数据库/端到端验收、34 个 Phase 2 回归、Ruff、mypy、迁移往返、业务摘要、前端与合约门禁全部通过 |
| 干净检出完整门禁 | PASS | 在 `/private/tmp/flow-phase3-clean.falAWa` 从锁文件安装后完成全部验收，无工作区未提交文件依赖 |
| `make stack-up` | PASS | API、Worker、Web、PostgreSQL、Redis、MinIO 六服务构建并达到健康状态 |
| API 运行时配置 | PASS | 容器内从 `/app` 加载 `flow.excel.v1`、9 组表别名和 6 条类型转换规则 |
| 标准/外部工作簿语义比较 | PASS | `semantic_differences` 为空，两者均匹配 Phase 2 已知答案 |
| 字段级血缘 | PASS | 两种来源各保留 57,633 个可定位源单元格和转换规则的值 |
| 批次生命周期与原子性 | PASS | 阻断、警告确认、发布回滚、修订版本和旧版本不可变性均有数据库验收覆盖 |
| OpenAPI 与 TypeScript 合约 | PASS | 9 个 intake 路径已发布，重新生成无漂移 |

## 双工作簿等价证明

| 项目 | FLOW 标准工作簿 | 外部物流工作簿 |
|---|---:|---:|
| 工作表数 | 10 | 9 |
| 源文件 SHA-256 | `af028bf7b183c3066d380c3886e5be9e3accd6ee27a3018d4d99ca5a06c54d94` | `99fc536d4efa1c791e063e93c0ec8dbf8f96f85c2f1d044488f573664143d24e` |
| 映射 SHA-256 | `e615c1d0ef677db10446ba3a14f7af14a5009ae778a80904f3c9faf6280856be` | `bca1bbe02ed67c74db2d50b143b36ebfa0e4d56415ea44b4453b26c7799d09a9` |
| 未解析必填字段 | 0 | 0 |
| 阻断问题 | 0 | 0 |
| 对账 | 全部通过 | 全部通过 |
| 已知答案 | 精确匹配 | 精确匹配 |
| 字段级血缘值 | 57,633 | 57,633 |

来源文件和映射哈希故意不同，证明两份结构不同的输入没有被误认为同一文件或同一映射；最终业务快照完全相同，证明下游语义不依赖外部 Excel 的工作表名称、列顺序、表头位置或显示格式。

两种输入得到的冻结分析摘要均为：

| 指标 | 精确值 |
|---|---:|
| 订单量 | 192,891.9451 |
| 履约件量 | 628,827.7397 |
| 收入 | 26,300,990.4095 |
| 直接成本 | 17,346,032.7562 |
| 毛利 | 8,954,957.6533 |
| 毛利率 | 0.340480 |
| 经营利润 | 6,708,895.8378 |
| 经营现金流 | 4,941,609.8078 |
| 现金转换率 | 0.736576 |

## 运行时故障修复证据

最初的完整栈 smoke 暴露了一个单元测试无法发现的部署差异：API 在导入 `intake.py` 时使用固定的 `Path.parents[6]` 推断仓库根目录，而容器中的模块路径只有 `/app/src/...`，因此在健康检查之前以 `IndexError` 退出。

最终修复不是改变父级数字，而是：

1. 从模块位置向上查找完整的三份 intake 配置，不再依赖固定目录深度；
2. 在 API/Worker 共用镜像中显式打包 Excel 契约、别名和转换规则；
3. 增加容器式浅路径布局与 Dockerfile 资源打包回归测试；
4. 重新构建完整栈，并在容器内实际加载配置。

修复后 API、Web 和 Worker smoke 均通过，说明验收覆盖了真实部署边界，而不仅是宿主机源码路径。

## 持久化与审计保证

- 原始工作簿以 SHA-256 内容寻址保存在 S3 兼容对象存储，相同字节安全复用，碰撞或元数据不一致时拒绝覆盖；
- 工作簿画像只读取结构和有限样本，不改写源文件；公式、异常压缩包、空文件和不支持格式被拒绝；
- 字段 ID、显示名、登记别名、兼容类型和可选 AI 建议按固定优先级形成版本化映射；AI 只能提出候选，不能改变契约或发布；
- 转换函数具有稳定规则 ID 和版本，保留 raw/transformed 值、源 sheet/row/column、理由与状态；
- blocking issue 不可确认绕过，warning 必须保留 actor、reason 和时间；
- canonical 事实按 import version 保存，批次发布在单一事务中切换正式版本；失败回滚不留下部分事实；
- 修订生成新版本，旧源文件、旧映射、旧质量结果、旧 canonical 行和旧血缘均继续可查询。

## 主要交付物

- 外部物流验收工作簿：`fixtures/workbooks/external_logistics_nonstandard_v1.xlsx`；
- 外部工作簿结构清单：`fixtures/intake/nonstandard_manifest.json`；
- 版本化别名和转换规则：`config/intake/`；
- 识别、映射、转换、质量、对账和编排实现：`services/api/src/flow_api/intake/`；
- Intake API：`services/api/src/flow_api/api/routes/intake.py`；
- 审计与版本化迁移：`0004_intake_audit`、`0005_versioned_facts`；
- 操作与错误说明：`docs/intake/flow-v1-intake.md`；
- 一键验收入口：`make test-intake-e2e`；
- 持续集成门禁：GitHub Actions `intake-e2e` job。

## 远端 CI

实现提交 GitHub Actions push run：<https://github.com/davyzhong/FLOW/actions/runs/33344368765>

该 run 包含 `unit`、`integration`、`static-python`、`static-web`、`contracts`、`migrations`、`smoke`、`data-contract` 和 `intake-e2e` 九个 jobs。本文档提交前要求九个 jobs 全部通过；最终结果与本文档提交对应的后续 run 一并作为 GitHub 历史保留。

## 边界与下一阶段

Phase 3 只负责把可信、版本化、可追溯的 canonical 批次发布到数据中间层。它没有在 API、驾驶舱或报告中临时计算经营指标。

Phase 4“Metric Snapshots”必须只读取已发布 canonical 版本，建立版本化指标定义和不可变 Metric Snapshot，精确计算月度、YTD、预算差异、同比和近 12 个月序列，并用 `fixtures/expected/known_answers.json` 及聚合不变量证明金额、比率和余额类指标的口径正确。
