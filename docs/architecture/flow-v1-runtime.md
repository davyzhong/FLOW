# FLOW V1 运行架构

## 进程与责任

| 进程 | 责任 | 依赖 | 生命周期所有者 |
|---|---|---|---|
| Next.js Web | Finance BP 工作台、交互和类型化 API 调用 | FastAPI | Web 应用 |
| FastAPI API | `/api/v1` 合约、领域用例入口 | PostgreSQL、Redis、MinIO | API 应用 |
| Celery Worker | 导入、指标计算、分析和发布后台任务 | Redis、PostgreSQL、MinIO | Worker 应用 |
| PostgreSQL 18 | 接入、标准事实、指标、证据和发布身份 | 持久卷 | 数据层 |
| Redis 8 | Broker、结果和幂等任务键 | 无 | 任务基础设施 |
| MinIO | 内容寻址的原始文件与报告文件 | 持久卷 | 对象基础设施 |

## 请求与数据边界

```text
Browser → FastAPI → application service → PostgreSQL / Redis / MinIO
                              ↓
                         Celery Worker

Raw Excel → intake/mapping/validation → canonical facts → metric snapshot
          → findings/evidence/review → report snapshot → publication attempt
```

只有接入模块能读取原始 Excel。任何驾驶舱、AI、指标计算或发布渲染必须从标准数据表或不可变快照读取，以避免不同输出产生不同口径。

## 运行与健康

`make stack-up` 构建并启动全部六个服务，等待 `5432`、`6379`、`9000`、`8000` 和 `3000` 可连接。API 和 Web 具备容器健康检查；Worker 由 Celery `inspect ping` 验证。

运行时秘密只来自环境变量。仓库内 `.env.example` 仅提供本地开发示例，生产部署必须覆盖数据库、Redis 和对象存储凭据。
