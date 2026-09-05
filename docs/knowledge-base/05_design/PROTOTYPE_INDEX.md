# FLOW 视觉原型索引

> 2026-09-04：本文登记历史设计原型；当前已实现页面请看[真实截图](../../assets/screenshots/README.md)与[项目 README](../../../README.md)。原型是方向依据，不代表当前代码已经达到全部视觉细节。

位置：[visual_prototypes](../03_assets/visual_prototypes)

这些 HTML 文件是浏览器视觉伴随工具保存的设计片段。它们用于记录设计过程，不是生产前端代码。

| 文件 | 内容 | 状态 |
|---|---|---|
| `information-architecture.html` | 导入、质量、驾驶舱、Investigation、报告的整体信息架构 | 结构通过，随后要求提高信息密度 |
| `dashboard-density-v2.html` | Finance BP 高密度经营驾驶舱 | 通过，作为驾驶舱密度基线 |
| `investigation-workspace.html` | 第一版结构化 Investigation | 用户选择加强证据与复核，后续被 V2 取代 |
| `investigation-evidence-v2.html` | 公式、口径、血缘、源行、审阅和发布门槛 | 有效方向，纳入正式设计 |
| `excel-import-workflow.html` | AI 识别、映射、清洗、校验和对账 | 流程保留，数据结构随后升级为标准中间层 |
| `canonical-data-layer.html` | 外部源、转换、标准层、指标层和发布层 | 通过，作为系统主干 |
| `standard-excel-package.html` | 初版标准 Excel 数据包 | 用户选择增强，后续被 V2 取代 |
| `standard-excel-package-v2.html` | 核心 + 财务扩展 + 物流扩展的模块化数据包 | 通过 |
| `unified-publishing.html` | PPT、Excel、HTML/PDF 的统一发布中心 | 通过 |
| `flow-v1-blueprint.html` | V1 完整产品蓝图、边界、错误处理和验收 | 通过 |
| `waiting-data-contract.html` | 从视觉讨论切换到数据契约讨论的等待页 | 过程记录 |
| `waiting-template-scope.html` | 确定模板增强范围时的等待页 | 过程记录 |
| `metric-library-v0-review.html` | 指标库 v0 评审台：40 通用 + 15 物流指标卡片、勾稽关系、CAS↔IFRS 映射、会计基础数据；支持逐项 纳入/待定/剔除 并复制筛选结果（由 `scripts/generate_metric_library_review.py` 从 v0 数据集 YAML 生成） | 评审中（D040 立项后的实施前确认） |

## 正式设计

正式设计规格的工作区权威版本：

[2026-08-29-flow-v1-design.md](../../superpowers/specs/2026-08-29-flow-v1-design.md)

本知识库同时保存归档时的快照：

[approved/2026-08-29-flow-v1-design.md](approved/2026-08-29-flow-v1-design.md)

如果两者未来不一致，以工作区权威版本和较新的决策日志为准，快照仅用于重建归档时状态。

