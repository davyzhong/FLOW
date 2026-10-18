---
doc_id: FLOW-VERIFY-SINGLE-MACHINE-RUNTIME-20261018-001
title: 单机运行结构收敛阶段验收记录
doc_type: verification
status: draft
version: 1.0
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: "[pending: codex/single-machine-runtime-convergence]"
evidence_refs: "[isolated-sqlite-schema-jobs-object-store-16, sqlite-settings-1, postgres-damai-reset-1, ruff, mypy, flow-bootstrap, isolated-init-health-200, docs-m6]"
applies_to: repository
---

# 单机运行结构收敛阶段验收记录

## 范围与结论

记录单机原型工作包第 3 阶段的本地实现与验收。该阶段已完成本地验收，待提交后的准确代码 SHA 通过 GitHub CI；因此目前不将阶段标为最终完成。测试和启动均使用隔离 SQLite/文件目录，未连接常驻业务库。

## 交付变化

- 默认结构化数据改为 `~/.flow/flow.sqlite3`，文件对象使用 `~/.flow/objects/` 本地内容寻址存储。
- 请求内同步执行分析任务并写入数据库状态；单机运行路径不再依赖 Redis/Celery。
- 上传、报告、导出与种子使用本地存储契约；运行依赖移除 Redis、Celery、MinIO/S3 SDK 与 PostgreSQL 驱动。PostgreSQL 测试/兼容路径保留在开发依赖中。
- 增加 SQLite 专用 Alembic 基线链，PostgreSQL 历史 migration 链保留不改。
- 增加 `scripts/flow.py`、`make flow-init` 与 `make flow` 单一初始化/启动入口；服务默认绑定本机地址。
- `make flow-bootstrap` 完成前端生产构建、standalone 静态资产复制、生产依赖裁剪和 Python 无开发依赖同步；明确设置 `CI=true` 让 pnpm 在无 TTY 的自动化环境完成裁剪。
- 历史 Compose 服务仅作为兼容性测试栈保留，并提供包含测试依赖的 API 测试镜像。
- 修复 Damai business reset 清理顺序以处理 ActionItem 外键，并增加 SQLite 重置后组织保留、业务数据清除和审核事件归档的往返测试。

## 验证证据

| 验证 | 结果 |
|---|---|
| 隔离 SQLite schema、初始化、种子重置及 Alembic 测试 | 16/16 通过 |
| SQLite jobs 与本地 object store 定向回归（包含于上项） | 通过 |
| SQLite 设置类型测试 | 1/1 通过 |
| PostgreSQL Damai reset 兼容测试 | 1/1 通过 |
| Ruff | 通过 |
| mypy | 213 个源文件通过 |
| 文档门禁 `python3 scripts/check_docs.py --phase m1` | 通过，327 文档、89 项旧版豁免、0 错误 |
| `make flow-bootstrap` | 完整通过，前端 production build、pnpm 生产依赖安装、uv `--no-dev` 同步均成功 |
| 隔离目录 `FLOW_DATA_DIR=/tmp/flow-damai-stage3-20261018-verify make flow-init` | SQLite 从空库升级至 `sqlite0004`，开发主体创建成功 |
| 同目录运行 `make flow` 并请求本地服务 | Web `/` HTTP 200；API `/api/v1/health` HTTP 200；受权限保护的 `/api/v1/operations/public-periods` HTTP 200 并返回期间数据，验证 SQLite 开发身份绑定可用 |

全量 API 回归此前用时 42 分 20 秒，结果 973 通过、2 失败、3 警告。两项失败已针对性修复并复验：PostgreSQL Damai 重置外键顺序及已移除运行时设置的旧契约测试。相应回归现为 2/2 通过。独立复核还发现通用开发身份种子会将数据库错误宽松跳过；单机初始化现启用严格模式，缺表或写入失败会中止初始化。使用无开发依赖的生产 Python 环境再次从空 SQLite 初始化，并请求受权限保护的经营期间 API 得到 200。没有据此重跑 42 分钟全套，准确 SHA GitHub CI 将提供本提交的全量门禁结果。

## 限制与下一步

1. 本地结论不代替准确 SHA CI；CI 通过后才关闭第 3 阶段。
2. 本记录状态保持 `draft`，待同 SHA CI 通过后按项目门禁改为 `verified`。
3. 下一项按唯一工作包顺序进入第 4 阶段：逐视图补齐 A+C 图表叙事和真实数据、趋势/对比、来源追溯与交互。截图采集/自动生成工作流仍按用户裁决暂停。
