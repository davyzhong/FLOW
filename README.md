<div align="center">

# FLOW

### 从 Excel 到可复核的财务分析与正式报告

面向物流与供应链企业 Finance BP 的财务分析工作台

**版本化数据 · 确定性指标 · 证据复核 · 冻结报告**

[快速开始](#快速开始) · [界面导览](#界面导览) · [系统架构](#系统架构) · [当前边界](#当前边界与下一步) · [文档中心](docs/README.md)

</div>

![FLOW Finance BP 驾驶舱：核心指标、趋势、利润桥、经营发现与毛利矩阵](docs/assets/screenshots/dashboard.png)

> 截图来自 `c1a59d1` 的真实页面和确定性物流演示数据，不是客户数据或设计效果图。文档核对日期：2026-09-04。当前阶段为 **Pilot Readiness（试点就绪建设）**，功能实现与生产部署验收分别记录。

## FLOW 解决什么问题

Finance BP 的月度工作通常横跨多份 Excel：业务量、收入与履约成本、财务实际、预算、应收和现金。FLOW 将这些文件转换为有版本、有质量检查、有血缘的数据，再用同一份指标与分析上下文支持驾驶舱、异常调查和报告输出。

项目长期方向是 Finance Intelligence OS。当前 V1 依据 [D039 产品定位](docs/knowledge-base/04_decisions/DECISION_LOG.md)，聚焦**财务数据收集与基于客观数据的准确财务分析**。涉及业务假设的经营归因和更广泛决策支持，保留为后续扩展；项目中的“经营驾驶舱”等页面名称沿用既有实现。

| 工作问题 | FLOW 的处理方式 | 可复核的结果 |
| --- | --- | --- |
| 工作表名称、列顺序、字段格式不一致 | 工作簿画像、别名映射、人工覆盖、版本化转换 | 映射版本、源文件 SHA、原始值与转换事件 |
| 业务收入与财务收入对不上 | 发布前质量检查与跨域对账 | 阻断项、警告确认原因、对账结果 |
| 页面数字与报告数字不一致 | 指标口径版本 + 指标快照 + 冻结报告内容 | 同一身份链、精确数值和计算轨迹 |
| 异常解释缺少证据 | 驱动贡献、公式、源记录、证据复核 | Finding、Evidence、Conclusion、追加式审阅事件 |
| AI 文字难以审计 | 受约束上下文、对象引用、数字一致性检查 | 结构化回答、降级原因、持久化交互记录 |
| 原报告重导出后内容发生变化 | 冻结完整 JSONB 视图，导出仅读冻结内容 | 稳定报告版本、独立发布尝试与下载校验 |

## 一张图理解工作流

```mermaid
flowchart TB
    subgraph Intake[01 数据接入与治理]
        direction LR
        A[外部 Excel / 标准数据包] --> B[画像与字段映射]
        B --> C[清洗 · 质量 · 对账]
        C --> D[发布标准事实]
    end
    subgraph Analysis[02 指标与证据分析]
        direction LR
        E[指标快照] --> F[确定性分析与 Findings]
        F --> G[驾驶舱与证据调查]
        G --> H[结论复核与批准]
    end
    subgraph Publishing[03 冻结与正式输出]
        direction LR
        I[冻结 Report Snapshot] --> J[PPTX / XLSX / HTML]
        I -. 需要注入打印器 .-> K[PDF]
    end
    Intake -. 服务层或演示脚本编排 .-> Analysis
    Analysis --> Publishing
    classDef data fill:#eaf3ff,stroke:#2463eb,color:#14243a
    classDef review fill:#ecf8f1,stroke:#2e8562,color:#14243a
    classDef output fill:#fff4df,stroke:#ac761f,color:#14243a
    class A,B,C,D,E data
    class F,G,H review
    class I,J,K output
```

实线表示已有领域处理关系；虚线标出尚需显式编排或部署集成的环节。当前“发布导入版本”只发布标准事实，**不会自动启动该批次的指标计算与分析运行**。演示初始化脚本会显式串联这些服务；不能将演示链路等同于任意上传文件后的自动全流程。

## 界面导览

当前浏览器入口包括 `/`、`/data`、`/investigations/{findingId}`、`/reports` 和 `/login`。驾驶舱与调查页采用高密度分析布局；导入、报告与登录页目前以功能完整性为主，视觉细化仍有空间。

### 1. Finance BP 驾驶舱

首页汇集八个核心指标卡、12 个月趋势、经营利润变动桥、重点 Findings、产品表现表和客户群 × 产品毛利矩阵。筛选维度包括期间、组织、客户群、物流产品和区域；进入调查时携带批次、指标快照和分析运行身份。

上方大图即当前驾驶舱。指标目录共 15 项，首页选择其中八项展示，不代表系统只有八个指标。

### 2. 数据工作台：把文件转换为可发布数据

流程为 **准备 → 上传与画像 → 映射确认 → 清洗与校验 → 发布**。

- 支持标准工作簿与非标准物流示例工作簿；
- 人工覆盖提交真实源文件 SHA，确认后继续使用已持久化的映射版本；
- 清洗结果显示转换、质量问题和财务对账；
- 警告必须填写确认原因，阻断项和未通过的对账必须处理；
- 发布后可下载标准化 XLSX，用于核对与交换。

<details>
<summary><strong>展开：字段映射界面</strong></summary>

![真实数据工作台的字段映射确认](docs/assets/screenshots/data-mapping.png)

</details>

![清洗与校验：转换统计、发布状态和财务对账](docs/assets/screenshots/data-quality.png)

### 3. Investigation：从发现回到证据

调查页提供异常定义、影响金额、驱动桥、计算明细、对账与质量状态、源记录、公式和数据血缘。结论分为**已验证事实、分析判断、待确认问题、建议行动**；批准由状态机控制。

![证据优先的 Investigation 页面](docs/assets/screenshots/investigation.png)

批准后的证据若被拒绝，或结论被修改，Finding 会退回复核并留下事件记录；没有证据的 Finding 不能批准。已冻结报告保留签发时内容，新的报告版本重新检查当前资格。

### 4. 报告中心：冻结、生成、追踪与下载

报告中心可以冻结已发布指标快照中的批准 Findings，选择报告版本和输出格式，查看各次生成尝试并下载成功产物。当前冻结表单需要填写指标快照 ID，尚未提供完整的可视化快照选择器。

![报告中心的冻结快照与格式选择](docs/assets/screenshots/reports.png)

截图展示已冻结的演示报告；没有用虚构的“生成成功”记录代替对象存储和 PDF 打印验证。

<details>
<summary><strong>展开：登录入口与移动端工作台</strong></summary>

![单用户登录入口](docs/assets/screenshots/login.png)

<img src="docs/assets/screenshots/data-mobile.png" width="390" alt="390 像素视口下的数据工作台" />

</details>

截图环境、数据来源和操作记录见 [界面截图说明](docs/assets/screenshots/README.md)。

## 能力与实现状态

| 模块 | 当前已实现 | 需要区分的边界 |
| --- | --- | --- |
| 数据接入 | 上传、画像、映射覆盖、清洗、警告确认、版本发布、标准化导出 | 任意新批次的指标/分析自动编排尚未接通 |
| 标准数据 | `flow.excel.v1`，10 张交换工作表，公共维度与主题事实 | Excel 是交换格式，PostgreSQL 是标准关系数据层 |
| 指标引擎 | 15 个指标、14 条依赖边、Decimal、月/YTD/预算/同比/T12 窗口 | 不支持的比较粒度不会伪造数值 |
| 分析引擎 | 5 个 typed Playbook、驱动对账、Finding 与 Evidence | 确定性政策与阈值，非自动学习模型 |
| 驾驶舱与调查 | 多维浏览、身份交接、证据复核、四要素结论、审阅历史 | 演示数据通过不替代真实客户试点 |
| Copilot | 上下文绑定、引用和数字校验、降级与持久审计 | 默认是离线 `DeterministicProvider`，尚无现成在线大模型适配器 |
| 报告发布 | JSONB 冻结内容、版本幂等、独立尝试、下载头与字节校验 | API 默认没有 PDF 打印器；PPTX/XLSX/HTML 仍依赖可用对象存储 |
| 单用户认证 | 登录、签名 cookie、代理鉴权、来源检查、退出、凭据轮换 | 非多租户/角色权限/SSO；生产仍需 HTTPS 与部署加固 |
| 异步基础设施 | Celery、Redis、任务身份与 Worker 健康检查 | Worker 示例任务仅返回 accepted，核心业务未全面接入队列 |

## 系统架构

### 运行组件

```mermaid
flowchart TB
    Browser[浏览器 · Finance BP] --> Web[Next.js 16 / React 19]
    Web --> Session[登录会话与同源 API 代理]
    Session --> API[FastAPI 模块化单体]
    API --> Intake[Intake / Canonical]
    API --> Metrics[Metrics / Analysis]
    API --> Review[Investigation / Copilot]
    API --> Publish[Publishing]
    Intake --> PG[(PostgreSQL 18)]
    Metrics --> PG
    Review --> PG
    Publish --> PG
    Intake --> S3[(S3 兼容存储 / MinIO)]
    Publish --> S3
    Worker[Celery Worker 基础设施] --> Redis[(Redis 8)]
    API -. 幂等任务基础设施 .-> Redis
```

| 层 | 技术与职责 |
| --- | --- |
| Web | Next.js 16.3.3、React 19.2、TypeScript、服务端同源代理 |
| API | Python 3.13、FastAPI、Pydantic、SQLAlchemy、Alembic |
| 计算 | Python Decimal、版本化 YAML 数据/指标/分析配置 |
| 文件 | openpyxl、python-pptx、HTML 渲染、可注入 PDF 打印器 |
| 存储 | PostgreSQL NUMERIC、S3 内容寻址对象、Redis |
| 工程 | pnpm 10.17.1、uv 锁文件、pytest、Vitest、Playwright、GitHub Actions |

版本以锁文件为准；系统是模块化单体加 Worker 基础设施，没有把每个领域拆成微服务。详见[运行架构](docs/architecture/flow-v1-runtime.md)。

### 身份、血缘与冻结边界

```mermaid
flowchart TB
    subgraph Data[源文件到标准事实]
        direction LR
        SF[Source File<br/>SHA-256] --> MV[Mapping Version<br/>映射内容身份]
        MV --> IV[Import Version<br/>批次与转换版本]
        IV --> CF[Canonical Facts<br/>源记录与字段血缘]
    end
    subgraph Analysis[标准事实到证据]
        direction LR
        MS[Metric Snapshot<br/>口径与引擎版本] --> AR[Analysis Run<br/>政策与运行身份]
        AR --> F[Finding + Evidence]
    end
    subgraph Report[证据到正式产物]
        direction LR
        RV[Review Event + Conclusion] --> RS[Report Snapshot<br/>冻结 JSONB / 内容版本]
        RS --> PA[Publication Attempt<br/>格式 / 状态 / 对象 SHA]
    end
    Data --> Analysis --> Report
```

三个关键约束：

1. **源文件与原始值保留。** 映射和转换产生版本，修订不覆盖旧数据。
2. **财务数字由确定性引擎产生。** AI 与渲染器引用结果，不另算一套数字。
3. **正式报告读取冻结内容。** 内容不变复用报告版本；变化生成新版本；失败重试使用原冻结视图。

### 复核状态与报告资格

```mermaid
flowchart LR
    A[候选 Finding] --> B[提交复核]
    B --> C{证据与结论符合要求?}
    C -- 否 --> D[补充证据 / 继续复核]
    D --> B
    B -- 审阅拒绝 --> R[rejected 终态]
    C -- 是 --> E[批准]
    E --> F[可进入新冻结报告]
    E -- 证据拒绝或结论修改 --> B
    F --> G[冻结内容不可变]
```

此图展示业务约束，精确状态和事件表见[领域对象](docs/architecture/flow-v1-domain-objects.md)。冻结与复核变更共享行锁，避免并发请求绕过资格检查。

## 数据契约与分析口径

### 一个工作簿，十张标准工作表

| 工作表 | 内容 |
| --- | --- |
| `00_填写说明` | 填写规则、口径和示例 |
| `01_分析批次` | 分析窗口、币种、实际和预算情景 |
| `02_经营实际` | 订单、件量、收入、直接成本 |
| `03_财务实际` | 管理科目对应的财务实际 |
| `04_月度预算` | 月度预算与业务维度 |
| `05_应收回款` | 应收、回款、现金相关事实 |
| `06_客户主数据` | 客户与客户群 |
| `07_物流产品` | 物流产品维度 |
| `08_组织与区域` | 组织和区域共用维度 |
| `09_管理科目` | 管理科目与财务映射 |

稳定字段 ID 决定语义，不依赖列顺序和展示名称。正式机器契约为 [flow_v1_contract.yaml](templates/excel/flow_v1_contract.yaml)，解释见[数据契约说明](docs/data-contract/flow-v1.md)。

仓库提供两份**带演示数据**的工作簿：[标准示例](fixtures/workbooks/flow_standard_v1.xlsx)、[非标准示例](fixtures/workbooks/external_logistics_nonstandard_v1.xlsx)。面向填写的治理模板可从数据工作台下载；不要把演示数据误当作空模板或真实业务账。

### 15 个版本化指标

| 主题 | 指标 |
| --- | --- |
| 规模 | 订单量、履约件量 |
| 收入与效率 | 收入、单均收入、直接成本、单均成本 |
| 盈利与履约 | 毛利、毛利率、履约成本率、经营利润 |
| 应收与现金 | 应收余额、回款率、经营现金流、现金转换率、应收账款周转天数 |

指标目录：[`flow.metrics.logistics.v1`](config/metrics/flow_v1_metrics.yaml)。金额和比率使用 Decimal/NUMERIC，区分流量与余额、比较窗口、允许维度和预算粒度。当前五个分析 Playbook 覆盖收入增长、毛利恶化、经营利润恶化、履约成本增加、应收与现金恶化；政策配置见 [flow-logistics-v1.yaml](services/api/config/analysis/flow-logistics-v1.yaml)。

## 快速开始

### 依赖

- Docker Desktop 或可用的 Docker Engine + Compose；
- Python **3.13** 与 `uv`；
- Node.js **24**；Make 和 Git；
- pnpm 由 Makefile 使用 `npx --yes pnpm@10.17.1` 调用，无需全局安装。

### 推荐：基础设施在容器，应用在本机

从一个新的开发数据库开始。以下命令不包含验收脚本的数据库清空动作。

```bash
git clone https://github.com/davyzhong/FLOW.git
cd FLOW
cp .env.example .env
make bootstrap

# 在当前 shell 导出刚复制的本地配置
set -a
. ./.env
set +a

make infra-up
(cd services/api && uv run alembic upgrade head)

# 可选：初始化确定性演示数据、12 个月指标快照和分析运行
(cd services/api && uv run python ../../scripts/seed_dashboard_demo.py)

make dev-api
```

另开一个终端，在仓库根目录加载同一份配置后启动 Web：

```bash
set -a
. ./.env
set +a
make dev-web
```

| 入口 | 地址 | 用途 |
| --- | --- | --- |
| Web 驾驶舱 | [localhost:3000](http://localhost:3000) | 演示数据浏览与调查 |
| 数据工作台 | [localhost:3000/data](http://localhost:3000/data) | 模板、上传、映射和发布 |
| 报告中心 | [localhost:3000/reports](http://localhost:3000/reports) | 冻结、生成和下载 |
| API 文档 | [localhost:8000/docs](http://localhost:8000/docs) | FastAPI 交互式接口文档 |
| API 健康检查 | [localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | 进程健康状态 |
| MinIO Console | [localhost:9001](http://localhost:9001) | 开发对象存储管理 |

`seed_dashboard_demo.py` 默认复用已有演示批次；加 `--fresh-batch` 会创建一个新的演示批次。它直接编排领域服务，不代表原始文件已实际上传到 S3。使用自己的工作簿时，先通过 `/data` 完成数据接入；当前无面向任意新批次的一键分析入口，后续指标/分析编排边界见上文。

### 全容器运行

在完成依赖、基础设施和数据库迁移后，可用 `make stack-up` 构建并启动 API、Worker、Web；`make stack-down` 停止 Compose 栈。不要与占用相同端口的本机应用同时启动。

当前 Compose 是开发基线。API 镜像的资源打包、真实存储与业务路径仍需要按目标部署验证，不能仅凭容器健康检查认定全部页面和发布路径已可用。迁移命令不由 `make stack-up` 自动执行。

## 登录与部署配置

默认两项凭据为空时是本地开发模式。启用认证时：API 和 Web 使用相同 `AUTH_TOKEN`；Web 额外设置独立的 `FLOW_WEB_PASSWORD`，并在生产环境设置 `FLOW_WEB_ORIGIN` 为真实公开访问地址。

```mermaid
sequenceDiagram
    participant U as 浏览器
    participant W as Next.js
    participant A as FastAPI
    U->>W: 登录密码（同源 POST）
    W->>W: 验证密码并签发会话
    W-->>U: HttpOnly / SameSite cookie
    U->>W: 业务请求 + 会话 cookie
    W->>W: 验签、有效期、写请求 Origin
    W->>A: 服务端附加 Bearer token
    A-->>W: 业务响应
    W-->>U: 数据或文件下载
```

| 变量 | 设置位置 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | API / Worker / 迁移进程 | PostgreSQL 连接 |
| `REDIS_URL` | API / Worker | Redis 连接 |
| `S3_ENDPOINT_URL`、`S3_BUCKET` | API / Worker | 对象存储地址与桶 |
| `S3_ACCESS_KEY`、`S3_SECRET_KEY` | API / Worker | 对象存储凭据 |
| `FLOW_API_INTERNAL_URL` | Web 服务端 | 内部 API 地址 |
| `AUTH_TOKEN` | API + Web | 相同的服务端共享 token |
| `FLOW_WEB_PASSWORD` | Web 服务端 | 单用户访问密码 |
| `FLOW_WEB_ORIGIN` | Web 服务端 | 如 `https://flow.example.com`，不含路径 |

密码与 token 不得放入 `NEXT_PUBLIC_*`。浏览器业务访问统一经同源代理，旧 `NEXT_PUBLIC_FLOW_API_URL` 配置已停用。会话有效期八小时，生产 cookie 使用 Secure；仅配置部分凭据会拒绝访问。详见[认证与会话说明](docs/operations/authentication.md)。

### 从旧版本升级

当前数据库迁移头为 **`0010_frozen_reports`**：

```bash
(cd services/api && uv run alembic upgrade head)
```

迁移不会为历史报告伪造冻结内容。没有 `frozen_view` 的旧快照仍可下载已经生成的产物，但不能重新渲染；需要从当前符合审批条件的数据重新冻结。数据库触发器阻止已冻结 payload 被改写。

## 开发、测试与验证

### 日常检查

```bash
make lint
make typecheck
make test-web
make contracts-check
```

修改 API schema 后执行 `make contracts`，检查生成的 OpenAPI/TypeScript 差异，再运行 `make contracts-check`。仅验证漂移时直接运行 check，不要先生成来掩盖未提交的差异。

### 分层门禁

| 命令 | 覆盖范围 | 环境与注意事项 |
| --- | --- | --- |
| `make test-web` | Vitest 组件、代理与会话测试 | 不需数据库 |
| `make test-api` | 全部 Python 测试 | 包含迁移和数据库清理，使用独立测试库及所需存储 |
| `make test-data-contract` | 工作簿与数据库语义往返 | 会启动开发基础设施 |
| `make test-intake-e2e` | 映射、质量、对账、发布与血缘 | 独立数据库 / S3 环境 |
| `make test-metrics-known-answers` | 指标精确已知答案 | 独立数据库 |
| `make test-analysis-invariants` | 分析政策与驱动不变量 | 独立数据库 |
| `make test-dashboard` | 页面、筛选、身份交接 | PostgreSQL + Playwright Chromium |
| `make test-investigation-e2e` | 调查与复核流程 | PostgreSQL + Playwright Chromium |
| `make test-copilot-evals` | 引用、数字、降级与审计 | 按脚本准备数据库 |
| `make test-publishing-golden` | 四格式关键值一致性 | Playwright Chromium 与领域测试环境 |
| `make test-user-closure-e2e` | 本地组合回归与用户入口冒烟 | 会启动服务；监督器仅清理本次启动的进程组，数据库仍须隔离。CI 由独立 job 覆盖前置门禁后仅运行闭环专属部分 |
| `make acceptance` | Phase 1–10 的七组组合验收 | **会清空 Compose `flow` 库的 public schema，不可用于业务库** |

需要浏览器门禁时安装仓库对应的 Chromium：

```bash
npx --yes pnpm@10.17.1 exec playwright install chromium
```

CI 定义见 [FLOW CI](.github/workflows/ci.yml)。无数据库 unit job 与需要基础设施的 integration job 已分开；本地定向验证、历史阶段验收、远端 CI 三种证据应分别阅读。最新运行请查看 [GitHub Actions](https://github.com/davyzhong/FLOW/actions)，不要把某次历史成功当作当前全量通过。

### 最近修复基线

`fa171ec`、`e688f1b`、`c1a59d1` 关闭两轮审查中的 R1–R9 与 N1–N3：冻结报告、证据资格、人工映射、警告确认、Copilot 审计与批次范围、PPT 正文、下载名称，以及认证和 CI 分组。

该轮记录包括前端 **42 项通过**、多个后端定向回归分组、迁移往返、生产构建、认证真实浏览器链路和独立代码复核。真实 MinIO 上传在该本机环境出现超时，未宣称其完整通过。分组存在重叠，不能相加成一个总测试数。完整证据见[修复验收](docs/implementation/2026-09-04-review-repairs.md)。

## 仓库导航

```text
FLOW/
├── apps/web/                 # Next.js 页面、组件、同源代理与浏览器测试
├── services/api/             # FastAPI、领域服务、模型、迁移和 Python 测试
├── packages/contracts/       # OpenAPI 与生成式 TypeScript 合约
├── config/                   # Intake 别名/转换、指标目录
├── templates/excel/          # flow.excel.v1 机器契约
├── fixtures/                 # 标准/非标准工作簿与确定性参考数据
├── infra/                    # Compose、容器构建文件
├── scripts/                  # 生成器、演示初始化与分层验收
└── docs/
    ├── README.md             # 全部文档导航与当前阅读路径
    ├── architecture/         # 运行架构、领域对象与血缘
    ├── data-contract/        # Excel 数据契约
    ├── intake/               # 接入、清洗与发布
    ├── metrics/              # 指标口径和快照
    ├── operations/           # 登录、认证与部署配置
    ├── implementation/       # 分阶段验收与修复证据
    ├── reviews/              # 历史代码审查及关闭状态
    ├── superpowers/          # 正式规格、阶段计划
    ├── assets/screenshots/   # 当前真实页面截图与来源说明
    └── knowledge-base/       # 项目状态、决策、交接与不可变档案
```

| 你想了解什么 | 推荐入口 |
| --- | --- |
| 全部文档与哪份是最新 | [文档中心](docs/README.md)、[文档状态登记](docs/documentation-status.md) |
| 产品为什么这样设计 | [正式 V1 规格](docs/superpowers/specs/2026-08-29-flow-v1-design.md)、[决策日志](docs/knowledge-base/04_decisions/DECISION_LOG.md) |
| 当前完成到哪一步 | [项目状态](docs/knowledge-base/00_start_here/PROJECT_STATE.md) |
| 新 Agent 接续 | [Agent 起点](docs/knowledge-base/00_start_here/AGENT_START_HERE.md)、[交接指南](docs/knowledge-base/07_handoff/CONTINUATION_GUIDE.md) |
| API 方法、路径与类型 | [API 路径索引](docs/api-reference.md)、[OpenAPI](packages/contracts/openapi.json) |
| 文件如何进入标准数据层 | [Intake 说明](docs/intake/flow-v1-intake.md) |
| 数字从哪里来 | [指标口径](docs/metrics/flow-v1-metrics.md)、[领域身份](docs/architecture/flow-v1-domain-objects.md) |

## 当前边界与下一步

```mermaid
flowchart LR
    A[Phase 1–10<br/>功能窄切片已实现] --> B[Pilot 1<br/>导入与报告页面已落地]
    B --> C[审查修复<br/>R1–R9 / N1–N3 已处理]
    C --> D[当前<br/>补齐部署与运行链路验收]
    D --> E[脱敏真实数据试点]
    E --> F[依据证据确定 V1.1]
    style D fill:#fff0cd,stroke:#aa7918,stroke-width:2px
```

下一步仍需完成：新导入批次的计算与分析编排、PDF 打印器和真实对象存储的目标环境验收、生产 HTTPS/网络边界/密钥管理、备份恢复演练、可观测性，以及脱敏真实物流数据试点。最小安全计划中的登录/API 认证已落地，不能据此把其余部署任务标为完成。

本仓库尚未提供独立的 LICENSE 文件；使用与分发授权请向项目维护者确认。贡献与协作遵循 [AGENTS.md](AGENTS.md)：先读项目状态和正式决策，保护原始档案，按风险验证，每个完整任务只提交相关文件并推送规范远端。
