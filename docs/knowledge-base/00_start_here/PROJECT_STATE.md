# FLOW 项目当前状态与时间线

## 当前状态摘要

截至 2026-08-30，产品设计、Phase 1“基础架构与对象契约”和 Phase 2“标准 Excel 数据契约与高拟真 fixture”均已完成。六服务栈可以从干净检出构建启动；`flow.excel.v1` 已冻结为首个可执行中间层交换契约，标准 Excel、确定性物流 fixture、已知业务答案、解析校验、PostgreSQL 持久化和再次导出均已落地。完整本地验收和 GitHub Actions 八个 jobs 全部通过。规范远程仓库为 <https://github.com/davyzhong/FLOW>；下一阶段是 Intake、Mapping & Quality。

## 阶段时间线

### 阶段 0：参考材料研究

用户最初围绕财务驾驶舱、经营分析、Excel 数据分析 Skill 和报告生成展开讨论，并提供五篇微信公众号资料。原始网页、正文、图片和研究笔记保存在研究目录中。

这一阶段形成的早期判断：

- 产品不应只是财务驾驶舱；
- 驾驶舱、Excel 分析和报告生成应是同一系统的不同界面；
- 产品需要数据、指标、分析、洞察和发布能力；
- 分析能力必须从描述和对比提升到诊断、预测和决策；
- Driver Model 比单纯图表模板更重要；
- 长期方向可以被描述为 Finance Intelligence OS。

### 阶段 1：产品目标收敛

用户明确：

- 不强求纯本地离线，Web、应用或其他部署均可；
- 工程名称候选包括 FLOW 和 FI 开头名称；
- 产品首先需要落到真实行业场景，而不是继续停留在抽象平台概念。

### 阶段 2：首个垂直场景

选择物流企业供应链业务，并以六张供应链规模日报截图作为经营结构参考。

关键场景决策：

- 使用高度拟真的模拟数据；
- 12 个月月度实际 + 年度月度预算；
- 核心故事是规模增长但盈利与现金恶化；
- 采用客户群 × 物流产品双维度；
- 保留组织、区域、客户和月份等辅助维度。

### 阶段 3：用户体验收敛

最初讨论过管理层和 Finance BP 双角色，用户随后明确撤回双角色首版，改为只做 Finance BP 视角的经营驾驶舱。

已确认：

- 首页采用“总览 + 异常 + 专题下钻”；
- 当月 + YTD 双视角；
- 经营和财务指标联动；
- 确定性计算 + AI 解读；
- 异常点击进入独立 Investigation；
- Investigation 以证据、公式、数据血缘和复核为核心；
- 驾驶舱采用高信息密度设计。

### 阶段 4：数据中间层确立

数据导入最初曾考虑只使用内置模拟数据，用户后来明确 Excel 上传、字段映射和数据清洗是 V1 必需能力。

进一步确立：

- 所有外部数据必须先转换到统一数据中间层；
- 标准 Excel 模板用于直接填写和外部数据转换核对；
- 数据库标准表是真正的数据中间层；
- 采用主题事实表 + 共用维度表；
- 标准 Excel 数据包采用一个多工作表文件；
- 模板采用“核心必需 + 财务扩展 + 物流扩展”的模块化结构。

### 阶段 5：统一输出层

用户明确 PPT、Excel 和正式月报不是后续附加能力，而是 V1 的重要组成。

已确认：

- 专业模板 + AI 编排；
- PPT 面向汇报和决策；
- 分析 Excel 面向复核和二次分析；
- HTML/PDF 月报面向签发和归档；
- 三种输出共享同一分析快照；
- AI 不重新计算数字；
- 未批准 Finding 不能进入正式报告。

### 阶段 6：完整设计批准

通过浏览器可视化原型依次确认：

- 信息架构；
- 高密度 Finance BP 驾驶舱；
- 证据优先的 Investigation；
- Excel 导入流程；
- 标准数据中间层；
- 模块化标准 Excel 数据包；
- 统一发布中心；
- FLOW V1 完整产品蓝图。

正式规格位于：

`docs/superpowers/specs/2026-08-29-flow-v1-design.md`

### 阶段 7：知识库归档

已保留全部有效原始资料并建立适合 Agent 接续的索引、决策日志和变更导航。历史研究源目录中除 `.mimosa` 运行状态外的 89 个文件，已与知识库归档逐文件核对一致。

### 阶段 8：规范仓库与持续交付约定

- 规范 GitHub 仓库：<https://github.com/davyzhong/FLOW>；
- 本地规范远程名：`origin`；
- 每个完整任务必须在验证后创建范围明确的提交并推送；
- 禁止强制推送和夹带无关用户文件。

### 阶段 9：详细实施计划

- 已建立 FLOW V1 主实施路线图，覆盖基础架构、数据契约、接入、指标、分析、驾驶舱、Investigation、AI、统一发布和运维验收十个阶段；
- 已完成 Phase 1“基础架构与对象契约”的可执行测试先行计划；
- 实施基线采用 Next.js Web + FastAPI 模块化单体 + Celery Worker + PostgreSQL + S3 兼容对象存储 + Redis；
- Phase 1 按测试先行计划开始实施。

### 阶段 10：Phase 1 基础架构与对象契约

- 建立 pnpm + uv 锁定依赖的 Next.js/FastAPI/Celery 工程；
- 建立 PostgreSQL、Redis、MinIO、API、Worker 和 Web 的 Compose 运行栈；
- 建立接入、版本、质量、血缘、8 个公共维度、4 个核心事实表；
- 建立指标快照、Finding、证据、评审、结论和统一发布身份；
- 发布 Workspace OpenAPI 与生成式 TypeScript 契约；
- 实现内容寻址对象存储和 Redis 幂等任务键；
- 迁移头达到 `0003_analytics_and_publishing`；
- 干净 worktree 验收通过，GitHub Actions 的 7 个 jobs 全部通过；
- 详细证据见 `docs/implementation/phase-1-verification.md`。

### 阶段 11：Phase 2 标准 Excel 数据契约与高拟真 fixture

- 冻结 `flow.excel.v1` 机器可读 YAML 契约，覆盖 10 张标准工作表；
- 生成可直接填写和导入的 `flow_standard_v1.xlsx`，以稳定字段 ID 而不是列位置或显示名称识别语义；
- 建立 24 个月、客户群 × 物流产品 × 组织 × 区域粒度的确定性物流供应链参考数据；
- 冻结收入、利润、现金、预算差额、应收与跨域对账的精确已知答案；
- 实现有类型的工作簿解析、空值语义、外键/粒度校验和错误报告；
- 实现 Excel → canonical package → PostgreSQL → canonical package → Excel 的零差异语义往返；
- 新增 `make test-data-contract` 与 GitHub Actions `data-contract` 门禁；
- 干净 worktree 完整回归通过，GitHub Actions 的 8 个 jobs 全部通过；
- 详细证据见 `docs/implementation/phase-2-verification.md`。

## 当前尚未完成

- 用户对正式规格文件的最后一次文档审阅；
- Phase 3–10 在各阶段开工前基于已验证接口形成可执行任务单；
- 指标字典、公式和阈值的完整明细；
- Excel 识别、字段映射、清洗、校验和发布工作流；
- Finance BP 驾驶舱、Investigation 和 AI Copilot；
- PPT、分析 Excel、HTML/PDF 报告渲染器；
- Phase 3–10 的功能实现与验收数据集；
- 正式品牌命名和 FLOW 的最终英文释义。

## 当前下一步

基于冻结的 `flow.excel.v1`、标准工作簿、确定性 fixture 和已知答案，形成并执行 Phase 3“Intake、Mapping & Quality”详细测试先行计划：完成不可变源文件存储、非标准 Excel 识别、确定性与 AI 辅助字段映射、版本化清洗审计、质量门禁和批次原子发布。
