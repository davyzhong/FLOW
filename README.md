# FLOW

FLOW 是面向物流与供应链企业 Finance BP 的 Finance Intelligence OS。V1 先把外部 Excel 转换为统一、版本化、可追溯的财务经营数据中间层，再由同一套标准数据驱动指标、分析、驾驶舱和正式报告。

## 运行架构

- Next.js Web：经营工作台与后续数据接入界面，端口 `3000`；
- FastAPI API：版本化领域 API，端口 `8000`；
- Celery Worker：异步导入、分析和发布任务；
- PostgreSQL：唯一标准关系数据与精确数值存储；
- Redis：任务代理和幂等任务键；
- MinIO：不可变原始文件与发布文件对象存储，端口 `9000/9001`。

原始 Excel 只能由接入层读取。指标、页面、AI 上下文和渲染器必须消费已发布的标准事实、指标快照和报告快照，不能直接读取原始文件。

## 本地启动

需要 Docker Desktop、Python 3.13、`uv` 和 Node.js 24。仓库使用锁定版本的 pnpm，无需全局安装。

```bash
cp .env.example .env
make bootstrap
make stack-up
```

服务入口：

- Web：<http://localhost:3000>
- API health：<http://localhost:8000/api/v1/health>
- Workspace contract：<http://localhost:8000/api/v1/workspace>
- MinIO Console：<http://localhost:9001>

开发模式可分别运行 `make dev-api` 和 `make dev-web`。停止容器使用 `make stack-down`。

## 验证命令

```bash
make test
make lint
make typecheck
make contracts-check
make phase-1-acceptance
```

`make phase-1-acceptance` 会启动完整栈，执行 Python/Web 测试、静态检查、OpenAPI 合约漂移检查、Alembic 三层迁移往返、HTTP smoke 和 Worker ping。

## 工程约定

- Python 依赖锁定在 `services/api/uv.lock`；前端依赖锁定在 `pnpm-lock.yaml`；
- 数据库变更必须提供 Alembic migration，并通过 `scripts/check_migrations.py`；
- OpenAPI 与 TypeScript 类型通过 `make contracts` 生成，提交前运行 `make contracts-check`；
- 每个完整任务只提交本任务范围的文件并推送到 `origin`。

进一步架构说明见 [运行架构](docs/architecture/flow-v1-runtime.md) 和 [领域对象](docs/architecture/flow-v1-domain-objects.md)。
