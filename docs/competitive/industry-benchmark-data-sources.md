---
doc_id: FLOW-INDUSTRY-BENCHMARK-SOURCES
title: 行业基准数据源调查 · 采购与接入方案
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
related: [./optimization-checklist.md, ./comparison-matrix-code-level.md, ./china-financial-bi.md]
---

# 行业基准数据源调查

> FLOW 当前最大缺口（详见 [optimization-checklist.md](optimization-checklist.md) P0-1.1）：杜邦拆解没有行业对照表，"高 / 低"无法判断。本文盘点可用数据源、采购建议、接入方案。

## 一、数据需求清单

FLOW 行业基准需要的数据：

| 数据类型 | 用途 | 颗粒度 | 时间窗口 |
| --- | --- | --- | --- |
| 行业 ROE 中位数 | 杜邦对比 | 行业 × 期间 | 5 年 × 季度 |
| 行业 ROE 标杆 | 行业领导力 | 行业 × 期间 | 5 年 × 季度 |
| 行业 ROE 末位 | 行业底线 | 行业 × 期间 | 5 年 × 季度 |
| 行业净利率 | 盈利水平对比 | 行业 × 期间 | 5 年 × 季度 |
| 行业资产周转率 | 营运效率对比 | 行业 × 期间 | 5 年 × 季度 |
| 行业权益乘数 | 杠杆水平对比 | 行业 × 期间 | 5 年 × 季度 |
| 行业毛利率 | 经营能力对比 | 行业 × 期间 | 5 年 × 季度 |
| 行业 ICR | 偿债能力对比 | 行业 × 期间 | 5 年 × 季度 |

## 二、数据源盘点

### 2.1 国内数据源

#### Wind（万得）

- **价格**：单账号 ¥39,800/年（≈$5,700）；批量（200+）折扣至 ¥24,540/年/账号
- **API**：Wind Python 接口 + C++/C#/Java/MATLAB/R/VBA 多语言
- **覆盖**：A 股 / 港股 / 美股 / 债券 / 基金 / 期货 / 期权 / 外汇 全市场
- **数据深度**：行业最权威，但价格最贵
- **私有部署**：❌（仅 SaaS / 终端）
- **接入方式**：本地 Wind 终端 + Python API，或 Wind 金融数据服务中心企业 API
- **适合**：头部金融机构（公募 / 头部券商 / 大型保险资管）
- **FLOW 接入成本**：¥20-50 万/年（按账号数估算）

#### 同花顺 iFinD

- **价格**：单账号 ¥0.9-2 万/年（个人版到专业版）
- **API**：Python / C# / C++ / Java / MATLAB / R / VBA + HTTP 接口
- **覆盖**：A 股 / 港股 / 美股 / 期货 / 基金 / 债券
- **数据深度**：弱于 Wind，强于 Choice
- **私有部署**：❌
- **接入方式**：iFinD 终端 + Python SDK
- **适合**：中小券商 / 私募 / 个人研究
- **FLOW 接入成本**：¥5-10 万/年

#### 东方财富 Choice

- **价格**：单账号 ¥3,160-5,800/年（团购价最低）
- **API**：Python / HTTP
- **覆盖**：A 股 / 港股 / 美股 / 基金 / 债券
- **数据深度**：基础数据 + 部分研报
- **私有部署**：❌
- **接入方式**：Choice 终端 + Python SDK
- **适合**：中小机构 / 高净值个人
- **FLOW 接入成本**：¥2-5 万/年
- **限制**：不提供 API 级别行业聚合数据（需要本地计算）

#### 通联数据 (DataYes)

- **价格**：按 API 调用计费 或 数据包年费 5-50 万
- **API**：REST API + Python SDK
- **覆盖**：基础金融数据 + 另类数据（电商 / 物流 / 出行 / APP）
- **数据深度**：另类数据是差异化优势
- **私有部署**：⚠（部分模块支持）
- **适合**：需要另类数据的研究机构
- **FLOW 接入成本**：¥10-30 万/年

#### 萝卜投研（通联）

- **价格**：含在通联数据套餐内
- **API**：自然语言查询 + REST API
- **覆盖**：A 股财报 + 研报 + 新闻
- **适合**：AI 问答应用
- **FLOW 接入成本**：含在通联套餐

#### 巨灵财经

- **价格**：定制
- **API**：REST API
- **覆盖**：基础财务数据 + 行业数据
- **优势**：第三方数据服务（非头部），数据来自交易所公开披露
- **FLOW 接入成本**：¥3-10 万/年

#### 优矿 / 米筐

- **价格**：免费 / 付费
- **覆盖**：量化因子库
- **FLOW 不直接对接**，但可借鉴因子设计

### 2.2 国际数据源

#### Bloomberg

- **价格**：$20,000-25,000/年/账号（不可议价）
- **API**：BQL（Bloomberg Query Language）+ Python API
- **覆盖**：全球全市场
- **FLOW 接入成本**：不适合（太贵）

#### Refinitiv (LSEG)

- **价格**：$12,000-22,000/年/账号
- **API**：Eikon Data API (Python) + DSS REST API
- **覆盖**：全球全市场
- **FLOW 接入成本**：不适合（贵）

#### S&P Capital IQ

- **价格**：$15,000+/年
- **API**：Capital IQ Web API + Excel Add-in
- **覆盖**：全球 + 行业深度
- **FLOW 接入成本**：不适合

#### Databento

- **价格**：历史数据 $1-5/GB；实时 $199-499/月
- **API**：REST + WebSocket，Python/Rust SDK
- **覆盖**：美股 + 期货 + 期权；不含 A 股 / 港股
- **数据深度**：HFT 级，原始 ITCH / MDP / OPRA
- **FLOW 接入成本**：$5,000-20,000/年

#### Massive (原 Polygon.io)

- **价格**：$29-449/月（按市场订阅）
- **API**：REST + WebSocket，Python SDK
- **覆盖**：美股 + 期权 + 外汇 + 加密
- **数据深度**：美股很好
- **FLOW 接入成本**：$1,000-5,000/年
- **优势**：开发者体验最佳，文档清晰

#### Barchart

- **价格**：小规模 $49/月起，企业定制
- **API**：REST + WebSocket
- **覆盖**：美股 + 期货；不含 A 股 / 港股
- **FLOW 接入成本**：$5,000-15,000/年

#### QuoteMedia

- **价格**：高端企业定制
- **API**：Streaming Data Feed
- **覆盖**：全球股票 + 期货 + 期权
- **数据深度**：机构级
- **FLOW 接入成本**：不公开（高）

#### EOD Historical Data

- **价格**：$19.99-99.99/月（个人 / 企业同价）
- **API**：REST
- **覆盖**：全球 70+ 交易所（含 A 股 / 港股）的历史数据
- **数据深度**：日线 + 分钟级
- **实时能力**：弱（主要是历史数据）
- **FLOW 接入成本**：$1,000-3,000/年
- **优势**：性价比高，含 A 股 + 港股历史
- **限制**：实时延迟，Level-2 数据缺失

## 三、采购策略建议

### 3.1 推荐组合（按预算分档）

#### 低预算（< ¥5 万/年）

```
主源：EOD Historical Data（全球历史日线 + 分钟）  ~$2,000/年
     巨灵财经（行业聚合 API）                       ~¥30,000/年
     自建爬虫（A 股财报 PDF 反向解析，已做）           ¥0
合计：¥5 万/年
覆盖：A 股 + 港股 + 美股，日线数据足够做行业基准
```

**适合**：早期客户验证 / POC

#### 中等预算（¥5-30 万/年）

```
主源：同花顺 iFinD（A股 + 港股）                     ~¥100,000/年
     EOD Historical Data（全球历史 + 分钟）         ~$3,000/年
     Databento（美股 / 期货原始数据，按需）          ~$5,000/年
     自建爬虫（5-10 家公司年报 PDF）                 ¥0
合计：¥15 万/年
覆盖：完整 A 股 + 港股 + 美股，全频段
```

**适合**：FLOW v2 路线（5-15 家公司，行业基准 + AI 问数）

#### 高预算（¥30-100 万/年）

```
主源：Wind 企业版（按账号）                          ~¥300,000/年
     Massive（美股期权 / 期货）                      ~$2,000/年
     Databento（HFT 数据）                          ~$10,000/年
     自建爬虫补全 + 数据 ETL 团队                   ¥0
合计：¥35 万/年
覆盖：全市场 + 全频段 + L1/L2 数据
```

**适合**：头部客户 / 标杆部署

### 3.2 关键决策点

| 决策 | 推荐 |
| --- | --- |
| A 股基准 | **iFinD**（性价比最高）/ Wind（最权威）/ 自建（成本最低但维护重）|
| 港股基准 | **iFinD** 或 **EODHD**（含港股历史）|
| 美股基准 | **Databento**（HFT 级）/ Massive（开发者友好）/ EODHD（低成本）|
| 国际物流基准（UPS / FedEx / DHL）| **Databento** 或 **Barchart**（美股原始）|
| 行业聚合数据 | **Wind**（最权威）/ 通联（差异化）|

### 3.3 不推荐的方案

| 方案 | 原因 |
| --- | --- |
| 全部用 Wind | 价格太贵，¥30 万+/年起，FLOW 短期承担不起 |
| 全部用爬虫 | 维护成本高、合规风险、覆盖率低 |
| 全部用 Choice | 数据深度不够，Level-2 / 衍生数据缺失 |
| 用免费 API（Yahoo Finance / Alpha Vantage）| 数据不全、有调用限制、稳定性差，不适合生产 |

## 四、接入方案

### 4.1 数据接入架构

```
┌────────────────────────────────────────────────────────┐
│ 数据采集层                                                │
│  - Wind Python SDK（同进程调用 Wind 终端）              │
│  - iFinD Python SDK（同进程调用 iFinD 终端）            │
│  - EODHD REST API（HTTP 调用）                          │
│  - Databento REST/WebSocket（HTTP/WS 调用）             │
│  - 自建爬虫（PDF 反向解析，已实现）                    │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 数据标准化层                                              │
│  - 统一指标 schema（finance.industry_benchmark.v1）    │
│  - 单位换算（万元 → 亿元 / 美元 → 人民币）             │
│  - 行业分类（证监会 / 申万 / 中信 / GICS）             │
│  - 异常值处理（极值 / 缺失 / 重复）                     │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 存储层                                                    │
│  - PostgreSQL（行业 × 期间 × 指标）                    │
│  - pgvector（嵌入 / 检索）                              │
│  - 文件存储（CSV / Parquet，按季度 partition）          │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 计算层（与现有 FLOW 指标引擎合并）                     │
│  - 杜邦三因子 / 五因子 / 二级子项                       │
│  - 行业聚合（均值 / 中位数 / 分位数）                  │
│  - 同比 / 环比 / CAGR                                    │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 展示层（前端 / 静态站 / 看板）                          │
│  - 杜邦对比矩阵 + 行业基准行                           │
│  - 排名表（按 ROE / 净利率 / 周转率 / 杠杆）           │
│  - 雷达图（5 维评估）                                   │
└────────────────────────────────────────────────────────┘
```

### 4.2 数据格式定义

```yaml
# config/benchmarks/industry_benchmark_v1.yaml
schema_version: 1
industry_classification: 中信一级行业
metrics:
  roe: "%"
  net_margin: "%"
  asset_turnover: "x"
  equity_multiplier: "x"
  gross_margin: "%"
  debt_ratio: "%"
  interest_coverage: "x"

data:
  - industry: 交通运输
    sub_industry: 物流
    period: 2025Q1
    snapshots: 8  # 8 家物流公司
    metrics:
      roe: { median: 8.5, p25: 4.2, p75: 12.3, top: 18.7, bottom: -2.1 }
      net_margin: { median: 4.2, p25: 2.1, p75: 7.8, top: 15.0, bottom: -1.5 }
      # ...

  - industry: 信息技术
    sub_industry: 软件
    period: 2025Q1
    snapshots: 12
    metrics:
      roe: { median: 12.0, p25: 6.5, p75: 18.2, top: 35.0, bottom: -5.0 }
      ...
```

### 4.3 定时任务

```python
# scripts/refresh_industry_benchmarks.py
"""每周日 02:00 刷新行业基准数据"""
import schedule
from datetime import datetime

def refresh_all():
    refresh_wind()           # Wind 数据
    refresh_ifind()          # iFinD 数据
    refresh_eodhd()          # EODHD 数据
    refresh_databento()      # Databento 数据
    refresh_company_pdfs()   # 自建 PDF 反向解析（5-10 家公司）
    aggregate_industry()     # 按行业聚合（均值 / 中位数 / 分位数）
    save_to_db()             # 写入 PostgreSQL
    notify_team()            # 飞书 / 邮件通知团队

schedule.every().sunday.at("02:00").do(refresh_all)
```

### 4.4 数据校验

```python
# scripts/validate_benchmarks.py
"""校验数据完整性 + 一致性"""
def validate():
    # 1. 缺失值检查：每个行业 × 期间 × 指标必须有值
    # 2. 异常值检查：ROE > 100% 或 < -100% 报警
    # 3. 同比变化检查：ROE 季度环比变化 > 30% 报警
    # 4. 跨数据源一致性：Wind vs iFinD vs 自建 PDF → 偏差 > 5% 报警
    # 5. 行业分类一致性：公司必须在唯一行业
```

## 五、合规与法律

### 5.1 数据使用合规

- **Wind / iFinD / Choice**：明确禁止对外分发。FLOW 内部使用 OK，对外发布需签"再分发"协议（贵）
- **Databento / Massive / Barchart**：API 授权可包含"再分发"条款，需核实
- **EODHD**：商业版含"再分发"，价格高
- **自建 PDF 反向解析**：法律边界模糊——可解析公开财报（合法），不能爬非授权源

### 5.2 建议方案

| 用途 | 推荐数据源 |
| --- | --- |
| FLOW 内部计算（杜邦 / 评分）| 任意（自用合规）|
| FLOW 客户内部使用 | Wind / iFinD / 自建 PDF |
| FLOW 客户对外发布（报告 / 网站）| 自建 PDF + 客户自有数据 |
| 公开 Benchmark 展示（FLOW 静态站）| 行业聚合的统计值（不显示原始公司数据）|

## 六、ROI 测算

### 6.1 价值评估

行业基准能直接补的 FLOW 能力缺口：

| 能力 | 商业价值 |
| --- | --- |
| 杜邦对比矩阵 + 行业行 | 直接卖单家客户 +5-15 万/年（基础模板）|
| 行业 ROE 排名 | 投研机构订阅 +10-30 万/年 |
| AI 问数（需要 benchmark） | 提升准确率 30-50%，客户黏性 + |
| 物流行业模板 | 单客户 +30-80 万/年 |

### 6.2 投入产出

| 投入 | 数值 |
| --- | --- |
| 数据采购（中等预算） | ¥15 万/年 |
| 工程接入（4-6 人月）| ¥25-35 万一次性 |
| 持续运营（0.5 人）| ¥5 万/年 |
| **总投入** | **¥45-55 万** |

| 产出（保守估计）| 数值 |
| --- | --- |
| 新增客户 | 5 家 × ¥20 万/年 = ¥100 万/年 |
| 现有客户升级 | 10 家 × ¥5 万/年 = ¥50 万/年 |
| **总产出（首年）** | **¥150 万/年** |

**ROI**：约 3-4 倍首年回本，第 2 年起纯利润。

## 七、实施路线图

### 7.1 Phase 1（4 周）— 自建 + EODHD

```
- 接入 EODHD API（A 股 + 港股历史数据）
- 自建 5 家重点公司 PDF 反向解析
- 行业聚合脚本（均值 / 中位数 / 分位数）
- 静态站加 benchmark 行
- 验证流程
```

### 7.2 Phase 2（4 周）— Wind / iFinD

```
- 接入 iFinD / Wind（按预算）
- 行业分类标准化（证监会 / 申万 / GICS）
- 行业聚合到 PostgreSQL
- 杜邦对比 API：GET /api/v1/industry-benchmark/{industry}
```

### 7.3 Phase 3（4 周）— 美股 + 国际

```
- 接入 Databento（美股原始）
- 加入 UPS / FedEx / DHL（国际物流 benchmark）
- 跨市场比较
- AI 问数接入 benchmark
```

### 7.4 Phase 4（持续）— 优化

```
- 每周日定时刷新
- 异常值自动告警
- 多数据源交叉验证
- 数据漂移监测
```

## 八、风险与缓解

| 风险 | 描述 | 缓解 |
| --- | --- | --- |
| 数据合规 | Wind / iFinD 不允许再分发 | 仅内部使用；benchmark 展示用统计聚合值 |
| 数据偏差 | 不同数据源对同一公司数据差异 | 交叉验证 + 偏差报警 |
| 覆盖率低 | 行业聚合要求足够样本数（≥ 5 家）| 优先扩 5-10 家公司 |
| 维护成本 | 数据需要持续刷新 | 自动化 + 0.5 FTE 维护 |
| 行业分类不一致 | 证监会 vs 申万 vs GICS | 提供多分类切换 |
| 异常值 | 极端值影响基准 | winsorize（1%-99% 截断）+ 中位数优先 |

## 九、立即可做（1 周内）

```bash
# 1. 注册 EODHD 试用账号（$19.99/月）
# 2. 接入 API 拉取 A 股 + 港股 5 年年报数据
# 3. 自建脚本生成行业聚合（均值 / 中位数 / 分位数）
# 4. 输出到 config/benchmarks/industry_benchmark_v1.yaml
# 5. 在 docs/library/index.html 的杜邦 section 加 benchmark 行
```

预算：**¥0**（试用账号）或 **¥2,000**（商业版）。

## 十、与现有 FLOW 架构整合

| 现有 | 整合 |
| --- | --- |
| `services/api/src/flow_api/metrics/calculator.py` | 复用指标计算引擎 |
| `services/api/src/flow_api/metric_library_store/coverage.py` | 复用 YAML schema |
| `scripts/p5_query_facts.py` | 复用 PDF 反向解析 |
| `docs/implementation/p5/statement_facts.yaml` | 复用事实库 |
| `config/metrics/*.yaml` | 复用指标字典 |

新模块：

```
services/api/src/flow_api/benchmarks/        # 新建
├── __init__.py
├── repository.py          # PostgreSQL 操作
├── aggregator.py          # 行业聚合（均值 / 中位数 / 分位数）
├── routes.py              # /api/v1/industry-benchmark/{industry}
└── scheduler.py           # 定时刷新

config/benchmarks/         # 新建
├── industry_classification.yaml
├── industry_benchmark_v1.yaml
└── companies_mapping.yaml  # 公司 → 行业 / 子行业
```

## 十一、监控指标

| 指标 | 目标 |
| --- | --- |
| 行业覆盖数 | ≥ 10 个中信一级行业 |
| 时间跨度 | ≥ 5 年 × 季度 |
| 数据源数 | ≥ 3 个（Wind + iFinD + EODHD + 自建） |
| 数据新鲜度 | ≤ 1 周（每季度财报发布后 1 周内入库）|
| 异常值告警 | ≤ 0.5% 数据点 |
| 跨源偏差 | ≤ 5% |
| 客户使用率 | ≥ 70% 客户使用 benchmark 功能 |

## 十二、总结

| 维度 | 推荐 |
| --- | --- |
| **主源（中等预算）** | iFinD（A 股 + 港股）+ EODHD（全球历史）+ 自建（重点公司 PDF）|
| **主源（高预算）** | Wind 企业版 + Databento + 自建 |
| **成本（中等预算）** | ¥15 万/年 |
| **成本（高预算）** | ¥35 万/年 |
| **ROI** | 3-4 倍首年回本 |
| **实施时长** | 12-16 周（分 4 个 phase）|
| **合规底线** | 仅内部使用 + benchmark 统计值展示 |

下一步（立即）：注册 EODHD 试用账号，1 周内跑通行业聚合 demo。

下次更新：2026-12（季度刷新数据源清单）