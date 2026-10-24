---
doc_id: FLOW-VERIFY-SINGLE-MACHINE-RUNTIME-20261018-001
title: 单机运行结构收敛阶段验收记录
doc_type: verification
status: verified
version: 1.1
created_at: 2026-10-18
updated_at: 2026-10-18
owner: FLOW
commit_refs: "[a2ce20644217ece4bae0635794b41f2256cedba7, 4c3e87e05ae9fe380abb7002ba260de6d654d15c, 20a511f66e4bfe65ab02edc091c7b49e2cbcbe67]"
evidence_refs: "[isolated-sqlite-schema-jobs-object-store-16, sqlite-settings-1, postgres-damai-reset-1, package-manifest-6, scripts-unittest-155, ruff, mypy, flow-bootstrap, isolated-init-health-200, docs-m1-m6, github-actions-39125304357-18-of-18]"
applies_to: repository
---

# 单机运行结构收敛阶段验收记录

## 范围与结论

记录单机原型工作包第 3 阶段的本地实现与验收。该阶段的最终状态提交 `20a511f66e4bfe65ab02edc091c7b49e2cbcbe67` 对应 GitHub Actions run `39125304357`，18/18 jobs 全部成功，第 3 阶段正式验收通过。所有测试和启动均使用隔离 SQLite/文件目录，未连接常驻业务库。

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
| 企业初始化发行包 manifest 专项测试 | 6/6 通过；同步重置 SQL 的 SHA256 与字节数 |
| Ruff | 通过 |
| mypy | 213 个源文件通过 |
| 文档门禁 `python3 scripts/check_docs.py --phase m1` | 通过，327 文档、89 项旧版豁免、0 错误 |
| `make flow-bootstrap` | 完整通过，前端 production build、pnpm 生产依赖安装、uv `--no-dev` 同步均成功 |
| 隔离目录 `FLOW_DATA_DIR=/tmp/flow-damai-stage3-20261018-verify make flow-init` | SQLite 从空库升级至 `sqlite0004`，开发主体创建成功 |
| 同目录运行 `make flow` 并请求本地服务 | Web `/` HTTP 200；API `/api/v1/health` HTTP 200；受权限保护的 `/api/v1/operations/public-periods` HTTP 200 并返回期间数据，验证 SQLite 开发身份绑定可用 |

全量 API 回归此前用时 42 分 20 秒，结果 973 通过、2 失败、3 警告。两项失败已针对性修复并复验：PostgreSQL Damai 重置外键顺序及已移除运行时设置的旧契约测试。相应回归现为 2/2 通过。独立复核还发现通用开发身份种子会将数据库错误宽松跳过；单机初始化现启用严格模式，缺表或写入失败会中止初始化。使用无开发依赖的生产 Python 环境再次从空 SQLite 初始化，并请求受权限保护的经营期间 API 得到 200。没有据此重跑 42 分钟全套，准确 SHA GitHub CI 将提供本提交的全量门禁结果。

首轮准确 SHA CI 发现大麦企业初始化包 manifest 未同步更新的重置 SQL 哈希与字节数；已只修正该 SQL 对应的清单项，未重生成或改动包内业务数据。发行包校验及其 6 项专项测试、完整脚本测试 155 项均通过。最终状态提交的全量 CI 18/18 通过。

## 限制与下一步

1. 第 3 阶段已关闭；准确 SHA CI 为 run `39125304357`（18/18 jobs success）。
2. 唯一队列已进入第 4 阶段子步 4.1：先完成参考文章 10 个模块与现有路由/API/指标/真实事实的覆盖映射，核实数据粒度、来源、图表和差距，再据矩阵顺序实施视觉与数据增强。
3. 截图采集/自动生成工作流仍按用户裁决暂停；阶段 4 采用浏览器交互与数据验收，不生成新截图。
