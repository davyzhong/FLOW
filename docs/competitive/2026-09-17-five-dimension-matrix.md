---
doc_id: FLOW-COMPETITIVE-MATRIX-5D
title: 竞对五维对比矩阵 · 功能/界面/体验/性能/交互（FLOW × 12 代表产品）
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-17
updated_at: 2026-09-17
owner: FLOW
related: [./summary-and-positioning.md, ./comparison-matrix-code-level.md, ./2026-09-15-frontend-patterns-research.md, ../knowledge-base/09_competitive/INDEX.md, ../knowledge-base/09_competitive/2026-09-14-optimization-backlog.md, ../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md]
confidentiality: project-internal
---

# 竞对五维对比矩阵（2026-09-17）

> 本文是既有竞对语料的**整合视图**：把 C01–C20 产品档案、代码级方法矩阵（D1–D17）、前端交互五轮调研、定位总汇与知识库第二截面新增素材，收拢为**功能 / 界面 / 体验 / 性能 / 交互**五个维度的一张对比矩阵，并给出 FLOW 现状（`defd823` 实测）与目标态差距的行动映射。不新增调研结论——单产品细节一律回链 C 档案；行动项一律回链 O-01～O-17 优化清单，避免第二份任务真相。

## 0. 方法与边界

- **证据等级**：竞对列 = 公开资料级（官网/官方文档/第三方评测，2026-09-11 调研 + 2026-09-17 AI 问数赛道快搜），**非产品实测**；FLOW 列 = 本仓实测（生产构建 e2e 56/56、单测 84/84、10× 性能基线 P95 数字）。
- **性能维度的诚实声明**：SaaS/私有化 BI 厂商不公开可比性能数据，竞对只做**架构级定性**（计算引擎路线）；FLOW 用实测数字。二者不在同一证据等级，不可直接排名。
- **评分符号**：●●● 该维度的行业标杆 / ●●○ 成熟 / ●○○ 有但弱 / ○ 未见到公开证据。评分对象是「公开可见的产品能力」，不是厂商整体实力。
- **竞对集合**：从 20 家档案中取 12 家代表（覆盖四赛道），其余见 [INDEX](../knowledge-base/09_competitive/INDEX.md)。

| 赛道 | 代表产品（档案） |
|---|---|
| 国际综合 BI | Power BI(C01)、Tableau(C02)、SAP AC(C04) |
| 国内综合 BI | 帆软 FineBI(C06)、Quick BI(C07)、观远(C08)、网易有数(C10) |
| FP&A/EPM | Anaplan(C11)、Board(C12)、Workday(C13)、先胜业财(C15) |
| 开源 BI/报表 | Metabase(C16)、Superset(C17)、DataEase(C19)、积木报表(C20) |

## 1. 五维总览矩阵

| 产品 | 功能广度 | 界面 | 体验 | 性能（架构级） | 交互 |
|---|---|---|---|---|---|
| Power BI | ●●● | ●●●（三栏配置态标杆） | ●●○（DAX 门槛高） | ●●●（Vertipaq 内存列式） | ●●●（交叉筛选联动范式） |
| Tableau | ●●● | ●●●（可视化美学标杆） | ●●○（分析自由度高=学习成本高） | ●●●（Hyper 引擎） | ●●●（VizQL 拖拽范式） |
| SAP AC | ●●●（财务语义最深） | ●●○ | ●●○ | ●●○（云模型） | ●●●（VDT 驱动树） |
| 帆软 FineBI | ●●●（财务模板最全） | ●●○ | ●●●（模板开箱即用） | ●●○（Spider 引擎） | ●●○ |
| Quick BI | ●●○ | ●●○ | ●●○ | ●●○（云数仓加速） | ●●●（自动归因 + 卡级 AI 解读） |
| 观远 | ●●○ | ●●○ | ●●●（卡片级洞察） | ●●○ | ●●●（卡级洞察+订阅推送） |
| 网易有数 | ●●○ | ●●●（PPT 式报告） | ●●○ | ●●○ | ●●○（报告级全局筛选） |
| Anaplan | ●●○（计划建模） | ●○○ | ●○○（建模者依赖） | ●●○（Hypersonic） | ●●●（假设-结果同屏） |
| Board | ●●○ | ●●○ | ●●○ | ●●○ | ●●●（因果链差异） |
| Workday | ●●○ | ●●○ | ●●●（使用者/建模者分离） | ●○○ | ●●○（任务待办首屏） |
| 先胜业财 | ●●○（国内 FP&A 最近邻） | ●●○ | ●●○ | ●○○ | ●●●（四步闭环） |
| Metabase/Superset/DataEase | ●●○ | ●●○ | ●●○（上手快） | ●●○（SQL 下推） | ●●○ |
| **FLOW（现状 `defd823`）** | ●●○（公开财报窄而深） | ●●○（两级 IA+token 体系） | ●●○（五态+引导+溯源） | ●●○（实测：10×10340 行 P95 明细 6.2ms/检索 0.97ms） | ●●○（页锚溯源点击+归因四问） |
| **FLOW（C 级出口目标态）** | ●●●（窄赛道内） | ●●● | ●●● | ●●●（已达标，随数据扩张复测） | ●●● |

## 2. 功能维（子维 × 代表竞对 × FLOW）

| 子维 | 行业标杆与机制（证据） | FLOW 现状 | 差距 → 行动 |
|---|---|---|---|
| 数据接入 | Power BI/帆软百种连接器；Anaplan 建模导入 | Excel 標準工作簿 + PDF 反向解析（14 份财报、670 事实） | 内部阶段才需 ERP 连接 → **O-15**（接口先定义不实现） |
| 语义层与指标治理 | Looker LookML、Qlik Master Items、SAC 科目树；行业共识「口径治理=可采信前提」 | **指标字典 YAML 一等公民（64+15 物流指标、口径/公式/责任组织）——FLOW 最强项之一** | 行业包扩展素材已备（借鉴 #21）→ 指标库 v1.x 候选 |
| 报表 | 帆软三大报表/CFO 驾驶舱模板族；积木类 Excel 复杂报表 | 四表一注 + 客观快照 HTML/PPTX/XLSX/PDF 同源发布 | 类 Excel 固定报表形态 → 已在 3b/报告中心 backlog |
| 驾驶舱 | 观远卡级洞察、Quick BI 一键解读、数据熊 11 模块单机范式（vault 簇 1） | Dashboard/Operations 六主题已上线；F3 收编 | 卡级 AI 解读入口 → **O-10/O-13** 关联 |
| AI 问数/归因 | Looker/Metabos 强制附定义+SQL；Quick BI 自动归因；2026 赛道关键词「从能回答到敢采信」（IDC：中国智能问数市场 180 亿元；主流=观远 ChatBI/小Q/有数/Power BI Copilot/FineBI NEXT） | **确定性问数 v1（94 问评测 100% 命中、拒答零误答）+ 引用链**——「敢采信」路线与行业风向同构；LLM 通道未接 | 语义上下文暴露+复算管线 → **O-01/O-02**（P1）；LLM 通道 v2 另行裁决 |
| 归因 | 三范式：Quick BI 全自动分解 / 永洪显式候选 / Board 传导链 | 四问「为什么」= 显式圈定 + 固定拆解（已采三范式组合） | 多维自动归因组件 → **O-10** |
| What-if/预测 | Pigment 滑块即时重算、Anaplan 同屏、Board 预测 | 无（D050 action 层，L2/L3 数据依赖） | → **O-14**（P3，按依赖解锁） |
| 发布订阅 | 观远订阅推送（企微/钉钉）、网易 PPT 式报告 | 四格式同源发布 + 报告中心 | 订阅推送 → **O-13**（P3）；报告级全局筛选 → 网易范式待评估 |
| 权限与审计 | SAC/Workday 企业级 RBAC；FLOW §3.3 身份合同 + 审计事件 | 角色绑定 + 不可变审计 + dev principal | 差异化强项（公开资料级竞对少有审计细节公开） |
| Excel 共生 | 帆软/观远 Excel 插件共生 | 标准模板导入 + 标准化工作簿导出 | 数字带溯源批注导出（E4，登记不排期） |

## 3. 界面维

| 子维 | 行业标杆 | FLOW 现状 | 行动 |
|---|---|---|---|
| 配置态/阅读态分离 | Power BI 三栏、DataEase 双设计器 | FLOW 无自助配置态（产品定位=确定性交付，非自助 BI，D052） | 不做自助设计器；驾驶舱配置化仅登记 |
| 信息架构 | Workday 角色分离、Ramp 工作流首屏 | 两级 IA（公开财报/内部经营分析）+ AppShell 全路由 | 首屏待办化（P-WorkbenchHome）→ 阶段三待领取 |
| 视觉系统 | Mercury 低密度/Stripe 高密度信任感 | --rep-* token + Tailwind v4（无 preflight）；F2 17 token 已补定义 | 56/56 门禁守护；密物表行级小按钮=密度例外已文档化 |
| 中国式复杂报表 | 积木类 Excel 设计器 | 无（公开财报四表为固定行列） | 不做（范围外） |
| 移动端 | 竞对普遍响应式弱（公开资料级未见标杆） | 390/1024/1440 三视口溢出门禁 + 44px 触控 | **FLOW 在移动端纪律上已领先公开资料级竞对**；保持门禁 |

## 4. 体验维

| 子维 | 行业标杆 | FLOW 现状 | 行动 |
|---|---|---|---|
| 上手成本 | 帆软模板开箱即用；Metabase 分钟级首问 | 种子数据 + 演示态（D045）；无模板市场 | 报告/驾驶舱模板族（借鉴 #19 簇 1 已登记） |
| 状态体系 | Workday 任务待办 | PageState 五态统一 + h1 稳定 + 恢复动作（P3） | 待办首屏 → 阶段三 P-WorkbenchHome |
| 引导与空态 | Carbon/Atlassian 三分类 | EmptyGuide 三分类全站 | 已达标 |
| 错误可理解性 | Looker 附定义+SQL；2026「敢采信」风向 | 中文 FlowApiError + 加载失败（状态码）+ 94 问拒答零误答 | 溯源链补真实来源链接（后端供稿决策待用户） |
| 角色分离 | Workday 使用者/建模者 | 经分专员/BP 双入口设计（D045/D053） | 缺失证据请求工作流 → **O-08**（P1） |

## 5. 性能维（诚实分级：竞对=架构定性，FLOW=实测）

| 产品/路线 | 引擎与规模声明 | 对照 FLOW 实测 |
|---|---|---|
| Power BI | Vertipaq 内存列式，亿级行桌面可交互 | FLOW 10× 数据集（1,034→10,340 行）P95：明细 6.2ms / 检索 0.97ms / 聚合 1.11ms（`perf_baseline.py`）——量级不同不可直接比，但**同数量级场景下 FLOW 指标在毫秒级** |
| Tableau | Hyper 列式 | 同上 |
| 帆软 | Spider 分布式 | — |
| Metabase/Superset | SQL 下推（性能=数据库的性能） | FLOW 同路线：PostgreSQL 下推 + typed API |
| **结论** | 架构路线（下推/列存）决定天花板；FLOW 的「确定性引擎+物化快照」在财报场景（万级行）已足够，性能瓶颈不在引擎而在抽取与解析 | C1 数据扩张到 80 份财报后复测 10× 基线（3b 已登记） |

## 6. 交互维

| 子维 | 行业标杆 | FLOW 现状 | 行动 |
|---|---|---|---|
| 筛选联动 | Power BI 交叉筛选 | Dashboard 期间/组织/客户群/产品/区域五维筛选 | 保持 |
| 下钻 | Tableau/SAC 层级下钻 | 四问下钻→证据→原文 | 驱动树 → **O-11**（P2） |
| 归因交互 | 三范式（见功能维） | 显式圈定+固定拆解 | **O-10** |
| What-if | Pigment 滑块 | 无 | **O-14** |
| 证据点击 | Stripe 完整性哲学 | 页锚溯源卡（95.5% 行项目）+ 点击展开/Escape/外点关闭 | 真实来源跳转 → 后端供稿决策（待用户） |
| 订阅推送 | 观远 IM 推送 | 无 | **O-13** |

## 7. 规划与设计调整建议（回答「知识更新后有什么调整」）

1. **路线不调整，证据与优先级微调**：知识库第二截面的 138 篇 HIGH（经营分析四体系/指标体系/报告框架）不改变「C 级出口 → T13 → 四级验证」主线，但把 T13 的设计输入从「待调研」变为「已备蓝本」（#20/#22/#24）——T13 解锁时设计周期可显著缩短。
2. **「敢采信」行业风向验证既有路线**：2026 ChatBI 赛道的差异化关键词（准确率/语义层/口径治理）与 FLOW「确定性引擎+指标字典+引用链」完全同构；O-01/O-02（语义上下文暴露+复算管线）应视为 C 级出口后 AI 问数 v2 的**必须项**而非加分项。
3. **指标库行业包升级为正式候选**：15 行业参考值 + 13 行业体系 + 美团实例（借鉴 #21）+ FLOW 已有 49+15 指标——建议在 C 级出口前或并行，作为低成本高确定性增项领取。
4. **移动端纪律作为差异化保留**：公开资料级竞对未见系统性移动端溢出门禁/触控标准，FLOW 的三视口+44px 门禁保持为长期门禁不放松。
5. **不做的事**：自助 BI 设计器（D052 范围外）、探索式分析（阶段三评估）、类 Excel 设计器（范围外）——矩阵再次确认这些「不做」与竞对差异是定位选择而非能力缺口。

## 8. 来源

- 单产品档案：[09_competitive C01–C20](../knowledge-base/09_competitive/INDEX.md)（2026-09-11 公开资料调研）
- 方法能力矩阵：[comparison-matrix-code-level v2.0](comparison-matrix-code-level.md)；定位：[summary-and-positioning](summary-and-positioning.md)
- 前端/交互五轮调研：[2026-09-15-frontend-patterns-research](2026-09-15-frontend-patterns-research.md)
- 行动清单：[O-01～O-17](../knowledge-base/09_competitive/2026-09-14-optimization-backlog.md)
- 知识库第二截面：[2026-09-17-obsidian-delta-scan](../knowledge-base/02_research/synthesis/2026-09-17-obsidian-delta-scan.md)
- AI 问数赛道快搜（2026-09-17）：[观远 ChatBI 官网](https://www.guandata.com/bi-copilot)、[2026 智能问数排行榜（IDC 市场 180 亿元）](https://www.163.com/dy/article/L2RPMLQP0556N1PR.html)、[衡石 ChatBI 选型指南](https://www.hengshi.com/blog/chatbi-platform-ranking-selection-2026.html)、[帆软 ChatBI 横评](https://www.finebi.com/uncategorized/2026%E5%B9%B4chatbi%E4%BA%A7%E5%93%81%E6%A8%AA%E8%AF%84)、[51CTO 八款评测](https://www.51cto.com/article/849063.html)
- FLOW 实测：perf_baseline.py、生产 e2e/单测（`defd823`）
