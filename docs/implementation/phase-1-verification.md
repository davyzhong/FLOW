# FLOW Phase 1 验证记录

验证日期：2026-08-30  
验证实现提交：`a0bf994b01a316648788be0ec16ad395f13a92ac`  
迁移头：`0003_analytics_and_publishing`

## 结论

Phase 1“基础架构与对象契约”验收通过。一个全新 Git worktree 可以从锁文件安装依赖、构建六服务运行栈，并通过静态检查、自动化测试、OpenAPI 合约、数据库迁移往返、HTTP smoke 和 Celery Worker 检查。GitHub Actions 对同一提交的七个 jobs 也全部通过。

## 干净检出验证

验证目录由 `git worktree add --detach` 从上述提交创建，目录中没有原开发 worktree 的 `node_modules`、`.venv` 或未跟踪文件。

| 命令 | 结果 | 证据摘要 |
|---|---|---|
| `make bootstrap` | PASS | pnpm 3 个 workspace 按锁文件安装；uv 安装 68 个包 |
| `make phase-1-acceptance` | PASS | 六服务构建、健康等待、全部门禁成功 |
| Python lint | PASS | Ruff 无错误 |
| Python typecheck | PASS | mypy 检查 27 个源码文件，无错误 |
| API tests | PASS | 30 passed |
| Web tests | PASS | 2 passed |
| integration tests | PASS | 17 passed |
| contracts check | PASS | OpenAPI 与 TypeScript 生成结果无漂移 |
| migration round trip | PASS | `upgrade head → downgrade base → upgrade head` 成功 |
| API/Web smoke | PASS | `8000/api/v1/health` 与 `3000/` 可访问 |
| Worker smoke | PASS | 一个 Celery 节点返回 `pong` |

## 远端 CI

GitHub Actions run：<https://github.com/davyzhong/FLOW/actions/runs/33287208460>

| Job | 结果 |
|---|---|
| `static-python` | PASS |
| `static-web` | PASS |
| `unit` | PASS |
| `integration` | PASS |
| `contracts` | PASS |
| `migrations` | PASS |
| `smoke` | PASS |

## 锁文件与主要运行版本

锁文件 SHA-256：

- `pnpm-lock.yaml`：`62677830f4249a04f268e97c9cb96f26055782ce2d08066f848753a267f07df2`
- `services/api/uv.lock`：`f0f4aa12da793dcd4d6302b96d79355df39105c6e76434cf33d34905f1e0a9a6`

应用层关键版本：FastAPI 0.141.1、SQLAlchemy 2.0.52、Celery 5.6.3、Pydantic 2.13.5、Next.js 16.3.3、React 19.2.0。

容器基线：

| 镜像 | 验证时摘要 |
|---|---|
| `postgres:18-alpine` | `sha256:d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2` |
| `redis:8-alpine` | `sha256:becdda6c7f4b3fb42e42fd7f120bbf5c54c4caaaf16f26da24e4563d2c1f0576` |
| `minio/minio:latest` | `sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e` |
| `minio/mc:latest` | `sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727` |
| `python:3.13-slim` | `sha256:7ce4b6dfe35e55397b7cda544f8a13f191b7ae28dc5aad71fe664dbc9bc2623f` |
| `node:24-alpine` | `sha256:e67514e5d0f6c46656005e1b693b2ec9d52e80b641307de684d4a015ba7a4eaf` |
| `ghcr.io/astral-sh/uv:0.10.10` | `sha256:cbe0a44ba994e327b8fe7ed72beef1aaa7d2c4c795fd406d1dbf328bacb2f1c5` |

## 已验证的 Phase 1 交付

- Next.js Web、FastAPI API、Celery Worker、PostgreSQL、Redis、MinIO 的可部署运行骨架；
- UUIDv7、Decimal 金额、状态枚举、对象引用和任务回执契约；
- 接入、版本、质量、对账和字段级血缘模型；
- 8 个公共维度与 4 个财务经营事实表；
- 指标快照、Finding、证据、评审、结论、报告快照和发布尝试模型；
- `/api/v1/health` 与 `/api/v1/workspace`，以及生成式 TypeScript 客户端契约；
- 内容寻址对象存储与幂等任务入队；
- 本地和 GitHub Actions 验收门禁。

## 非阻断限制与下一阶段

- MinIO 仍使用 `latest` 标签，但本记录保存了验证时镜像摘要；进入生产部署设计时应固定版本标签或 digest；
- GitHub Actions 对部分第三方 action 显示 Node.js 20 弃用提示，但 runner 已强制使用 Node.js 24，未影响验证结果；后续跟随 action 的新版 runtime 更新；
- Phase 1 只建立系统骨架与稳定对象契约，尚未生成 FLOW 标准 Excel 实体、模拟数据、导入映射工作流和 Finance BP 驾驶舱；
- 下一步是依据已验证的 schema 与 API 编写并执行 Phase 2“标准 Excel 数据契约与高拟真 fixture”详细计划。
