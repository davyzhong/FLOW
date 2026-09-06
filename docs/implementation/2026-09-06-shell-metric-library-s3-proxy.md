# 2026-09-06 统一导航、指标库入系统与 S3 代理根因修复

## 背景

用户从桌面端会话移交后提出三个问题：

1. 除 `/statements` 外所有页面没有左侧菜单，整体风格混乱；
2. 财务指标库（D040 的 v0 草案）不在系统里；
3. 此前完成的多个功能无法使用。

## 诊断结论

| 问题 | 根因 |
| --- | --- |
| 左侧菜单缺失 | `WorkflowNav` 只在驾驶舱成功态与 `/statements` 渲染；`/data`、`/reports`、`/investigations` 及驾驶舱错误/空态均无导航；调色板变量作用域限于 `.dashboard-app` |
| 「分析与归因」导航 404 | 导航指向 `/investigations`，但只有 `/investigations/[findingId]` 路由，且无 Finding 列表 API |
| 指标库不在系统 | v0 数据集只存在于知识库 synthesis 与静态评审台 HTML，未进入运行时 |
| 驾驶舱 404 | 当前数据库无已发布指标快照（`dashboard_not_ready`），重新播种演示数据即恢复 |
| `/data` 上传卡死 | **boto3 经 `getproxies()` 拾取 macOS 系统代理（127.0.0.1:1082），代理进程未运行时 MinIO 请求被送入死代理挂起**；这就是历史记录中「真实 MinIO PutObject 超时」的根因。绕过代理后上传 0.14s 完成 |
| 报告中心难用 | 冻结表单要求手填 metric snapshot ID，无选择器 |

## 变更内容

### API（services/api）

- 新增 `infrastructure/s3_client.py`：`build_s3_client` 统一构造 boto3 S3 客户端，默认禁用系统代理（`Config(proxies={"http": None, "https": None})`），带 connect 5s / read 60s 超时；`S3_USE_SYSTEM_PROXY=true` 可恢复旧行为。intake、publishing 路由与 publication 服务三处构造点全部切换到该工厂；
- `settings.py` 新增 `s3_use_system_proxy: bool = False`；
- 新增 `GET /api/v1/metric-library`（只读，加载 `config/metrics/metric_dictionary_v0.yaml` 与 `accounting_foundation_v0.yaml`，lru_cache；公式支持嵌套与数值参数）；
- 新增 `GET /api/v1/investigations`（Finding 列表，携带批次/快照/运行完整身份，D036）；
- 新增 `GET /api/v1/publishing/freeze-candidates`（已发布快照 + 期间标签 + 已批准 Finding 数）。

### 数据配置

- `config/metrics/metric_dictionary_v0.yaml`、`config/metrics/accounting_foundation_v0.yaml`：从知识库 synthesis 草案复制为系统配置（draft 状态保留，口径变更走版本化）。

### Web（apps/web）

- 新增 `components/shell/app-shell.tsx`：全部功能页共享的导航外壳（含调色板变量），1200px 以下导航折叠为图标；
- `WorkflowNav` 增加「指标库」入口，激活匹配改为前缀匹配（`/investigations/{id}` 高亮「分析与归因」），新增 library 图标；
- `/data`、`/reports`、`/investigations/[findingId]` 接入外壳；驾驶舱错误/空态接入外壳（加载态保持原几何，避免视觉基线漂移）；
- 新增 `/metric-library` 页面：通用/物流指标卡片（公式、时间行为、CAS/IFRS 取数、依赖、MPM、口径与来源）、勾稽关系、取数映射表、会计基础（科目表搜索、准则登记册、分录模板、已知缺口）；
- 新增 `/investigations` 列表页：全部 Finding 的状态/影响/评分与身份交接链接；
- 报告中心冻结表单改为下拉选择（无已批准发现的快照禁用并标注），首次冻结后自动选中新快照。

### 测试

- 新增 `tests/api/test_metric_library_api.py`（无 DB 契约测试：55 指标 / 28 映射 / 3 关系 / 164 科目等结构锁定）；
- `test_investigations.py` 新增 Finding 列表身份完整性用例；`test_publishing_api.py` 新增 freeze-candidates 用例；
- 修复回归：`usePathname()` 在单测环境返回 null 导致的崩溃（防御性处理）；冻结候选解析对 404/异构响应容错；React 严格模式 abort 误报为错误。

## 验证证据

- API 回归：`test_publishing_api.py` + `test_investigations.py` + `test_workspace.py` + `test_auth_boundary.py` + `test_metric_library_api.py` 共 14 项通过；Web Vitest 45 项通过；`make lint`、`make typecheck`、`make contracts-check` 通过；
- 浏览器全链路（真实 MinIO）：`/data` 上传标准工作簿 → 映射确认 → 清洗校验 → 发布成功；调查列表 → 进入工作台（身份随链接交接）；Finding 经 API 完成证据核验/结论/批准后，报告中心下拉选择 2026-08 快照 → 冻结 → 生成 HTML+XLSX → 下载成功（服务端命名，字节校验在既有黄金门禁覆盖）；
- 注意：`tests/` 默认以开发库 `flow` 为测试库（conftest 固定 URL），运行 API 测试会清空开发库数据，之后须重新执行 `scripts/seed_dashboard_demo.py` 恢复演示数据。

## 边界与后续

- 指标库为 v0 草案只读视图；逐项评审与 P1–P5 实施按 D040/D041 规格推进；
- `/data` 与 `/reports` 视觉仍是功能优先，深化留待专门设计任务；
- 任意新批次的指标/分析自动编排仍未接通（与 README 既有说明一致）；
- PDF 默认无打印器，状态如实为 failed 可重试。
