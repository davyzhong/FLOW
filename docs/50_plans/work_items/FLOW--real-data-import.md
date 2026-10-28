---
doc_id: FLOW-WI-REAL-DATA-IMPORT-20261028-001
title: 真实数据导入（单机原型从演示走向可用）
doc_type: work-item
status: active
version: 1.0
created_at: 2026-10-28
updated_at: 2026-10-28
owner: FLOW
depends_on: [FLOW-WI-SINGLE-MACHINE-VISUAL-20261018-001]
acceptance_refs: []
applies_to: services/api, apps/web
decision_refs: [D055]
knowledge_release: flow-knowledge-2026-09-12.1
supersedes: []
superseded_by: null
source_refs:
  - docs/50_plans/work_items/FLOW--single-machine-visual-prototype.md
confidentiality: project-internal
---

# 真实数据导入（单机原型从演示走向可用）

## 目标

让单机原型从「只能看大麦 synthetic 演示数据」升级为「能导入用户自己的财务数据并生成驾驶舱」，补齐原型走向日常可用工具的最大缺口。

## 背景

D055 单机原型已交付：SQLite 单文件、一键启动、九页 CFO 驾驶舱、图表下钻、报告导出、备份恢复——但数据面只有大麦演示包（synthetic）。用户无法把自己的财务数据放进去看自己的经营分析。

K3 知识刷新已于 2026-10-28 由用户裁决挂起（批次 134–162 共 696 条审毕推送，剩余 7,813 条挂起），主线转产品功能；本工作包为用户裁决后的新队首。

## 范围与批次

### R1 导入模板与校验引擎（后端）

- 定义三张 Excel/CSV 导入模板：**科目余额表**（期初/期末余额）、**利润表**（月度或多期）、**银行/现金流流水**（可选，第一期可后置）。
- 模板字段采用通俗中文列名 + 内置示例行；提供模板下载（静态 xlsx 生成脚本）。
- 校验引擎（Decimal 全程）：借贷平衡（资产=负债+权益）、必填列、日期格式、重复期间检测；错误逐行报告（行号+原因），不合格整批拒绝。
- 单元测试：合法样例全通过、典型错误各一（不平衡/缺列/坏日期/重复期间）。

### R2 导入 API 与账套装载（后端）

- `POST /api/import/dataset`：上传文件 → 校验 → 写入 SQLite 独立 schema（与演示数据隔离，按 dataset_id 区分）。
- 导入成功后复用现有归一化/驾驶舱投影链路，生成指标快照与九页数据。
- 每数据集可整体删除重导（幂等）；演示数据与导入数据可切换查看。
- 隔离测试：不触碰常驻库，临时目录 SQLite。

### R3 导入向导 UI（前端）

- 新页面 `/data/import`（AppShell 内 + 导航登记 + e2e 清单更新）：模板下载 → 上传 → 校验报告（错误逐行展示）→ 成功后跳转驾驶舱（切换到该数据集）。
- 五态齐全（loading/empty/error/ready/degraded）；契约更新走 `make contracts-check`。

### R4 验收

- 端到端：下载模板 → 填入样例数据 → 导入 → 九页驾驶舱出数 → 导出报告数值一致。
- 异常路径：不平衡文件被拒且错误定位到行。
- 浏览器验收 + 准确 SHA CI 全绿。

## 不做什么

- ❌ 多币种、合并抵销、预算编制（后续迭代）
- ❌ 自动科目映射 AI（第一期用固定模板列名，用户按模板填数）
- ❌ 连接常驻 PostgreSQL/外部数据库（保持单机 SQLite 边界）
- ❌ 改动大麦演示数据链路（隔离共存）

## 边界与红线

- 不触碰 ObsidianWiki、不恢复 K3（用户已裁决挂起）。
- 不删除文件、不改 CI 配置、密钥不进代码。
- 每批次：门禁全绿 → 提交 → 立即推送。

## 依赖关系

R1 → R2 → R3 → R4（严格串行）

## 关联文档

- 上游原型：[FLOW--single-machine-visual-prototype.md](FLOW--single-machine-visual-prototype.md)（completed，回归基线）
- 唯一队列：[CURRENT_ROADMAP](../CURRENT_ROADMAP.md)
