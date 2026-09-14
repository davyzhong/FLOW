---
doc_id: FLOW-COMPETITIVE-AI-OS
title: 开源 AI 财务分析生态 · 调研
doc_type: competitive-research
status: current
version: 1.0
created_at: 2026-09-15
updated_at: 2026-09-15
owner: FLOW
related: [./README.md, ./summary-and-positioning.md]
---

# 开源 AI 财务分析生态

> 调研时点：2026-09-15。覆盖 GitHub Star ≥ 1k、面向"财务 / 财报 / 投资研究"的活跃开源项目。

## 一、市场观察

2024-2026 是 AI × 财分开源项目的爆发期。三股力量叠加：

1. **LLM 普及**：GPT-4 / Claude / 通义千问让"自然语言问财务数据"可行
2. **本地化 / 数据合规**：中国 / 欧洲金融客户对私有部署需求强烈，纯 SaaS 难落地
3. **分析师薪资贵**：投资 / 投行 / 审计行业的人月成本持续上行，"AI 替人"是真痛点

## 二、头部项目盘点

### 1. OpenBB Terminal (⭐ 41k+)

- **定位**：开源投资研究终端，原名 Gamestonk Terminal，覆盖股票 / 期权 / 加密 / 衍生品 / 宏观经济
- **数据模型**：基于 pandas / numpy 的本地数据缓存（CSV / Parquet），支持从 Yahoo Finance、FRED、SEC EDGAR、Binance 等多源拉取
- **分析能力**：内置 300+ 命令（`/disc` 发现、`/fa` 财务、`/ta` 技术、`/bt` 回测）；杜邦属于 `/fa` 子模块的衍生
- **可视化**：matplotlib / plotly 静态图 + Rich 终端彩色输出
- **AI 能力**：2025 年集成 OpenAI / Anthropic SDK，支持"问数"（"为什么 AAPL 的 ROE 突然下降？"）
- **技术栈**：Python 3.10+、Poetry、Ruff；终端 UI 用 Rich + Textual
- **商业模式**：开源 + 商业版 OpenBB Workspace（云端协作）
- **对 FLOW 启发**：
  - ① "命令式 + 终端 + 快速回测" 的分析师风格，对内部用户的「资深财务 BP」友好；FLOW 不走这条路（要的是 GUI）
  - ② 「数据源路由 + 标准化事实」是值得借鉴的：每个 item_id 对应一个 source provider
  - ③ AI 问数能力（Q&A）方向值得加到 FLOW 未来路线图

### 2. FinGPT (⭐ 17k+)

- **定位**：金融大语言模型开源项目（港中深 PhD 项目），主打开源 LLaMA 微调在金融语料
- **数据模型**：基于 Hugging Face Transformers；数据集爬取财报 / 公告 / 研报 / 社交媒体
- **分析能力**：情感分析、命名实体识别（识别财报里的人名 / 公司名 / 金额）、文本摘要
- **可视化**：无原生可视化，纯文本生成
- **AI 能力**：本身就是 LLM，所有能力围绕"理解金融文本"
- **技术栈**：PyTorch + LoRA + Hugging Face Trainer
- **商业模式**：纯学术，无商业版
- **对 FLOW 启发**：
  - ① 中文金融语料稀缺，多数 LLM 在中文财报上不如英文财报准确
  - ② 摘要能力可以集成到 FLOW 的 MD&A 自动生成（"基于本期 14 份财报生成经营快照文字版"）
  - ③ 不依赖其代码（学术导向），但数据标注经验值得借鉴

### 3. FinRL (⭐ 11k+)

- **定位**：深度强化学习在量化交易中的应用（哥伦比亚大学 + 香港大学等学术项目）
- **数据模型**：DataFrame + gym 环境；DOW30 / NASDAQ / CSI300 / 港股等
- **分析能力**：单只股票择时、组合再平衡、回测引擎、对比 baseline
- **可视化**：backtesting.py + matplotlib
- **AI 能力**：训练 PPO / A2C / DDPG / SAC 智能体做交易决策
- **技术栈**：PyTorch + Ray RLlib + Zipline
- **商业模式**：纯学术
- **对 FLOW 启发**：
  - ① 与 FLOW 不重合（FLOW 不做交易）
  - ② 但 RL 框架中"环境—状态—动作—奖励"的拆解思路可用于经营决策支持："如果降低某公司杠杆 0.5x，对 ROE 的影响是？"
  - ③ 杜邦敏感性分析的另一种实现路径

### 4. FinanceToolkit (⭐ 3k+)

- **定位**：Python 库，集成 150+ 财务比率计算 + 模型估值（DCF / DDM / WACC）
- **数据模型**：基于本地 / 远程 CSV / DB；输出标准化 DataFrame
- **分析能力**：盈利质量、流动性、偿债能力、效率、估值比率；杜邦属于 `ratios` 子模块
- **可视化**：matplotlib
- **AI 能力**：无
- **技术栈**：纯 Python 库
- **商业模式**：开源，无商业版
- **对 FLOW 启发**：
  - ① 150+ 比率的实现可作 FLOW 指标字典 v2 拓展时的参照列表
  - ② 估值比率 / 风险比率目前 FLOW 不涉及，未来可作为 v2 路线

### 5. QuantStats (⭐ 6k+)

- **定位**：量化分析报告自动生成（HTML / PDF），对接 Zipline / Backtrader / QuantConnect
- **数据模型**：基于净值序列（NAV Series）
- **分析能力**：Sharpe / Sortino / Calmar / 最大回撤 / 胜率等组合绩效指标
- **可视化**：plotly 报告
- **AI 能力**：无
- **技术栈**：Python + Plotly + QuantLib
- **商业模式**：开源
- **对 FLOW 启发**：
  - ① "一键 HTML 报告" 输出体验值得借鉴（FLOW 已有 `docs/library/index.html`）
  - ② 组合绩效报告的"指标体系 + 自动图"模式与 FLOW 杜邦分析范式一致

### 6. Beancount / hledger / Ledger（命令行复式记账）

- **定位**：纯文本复式记账工具（个人 / 小团队财务记录）
- **数据模型**：双账户 + 借贷记账的纯文本；账本是可读 CSV-like
- **分析能力**：内置 `bean-report` / `hledger-bal` 等命令输出资产负债表、利润表
- **可视化**：依赖外接工具（如 Fava 网页 UI）
- **AI 能力**：无原生
- **技术栈**：Beancount（Python）/ hledger（Haskell）/ Ledger（C++）
- **商业模式**：开源
- **对 FLOW 启发**：
  - ① "纯文本 + 强类型账本" 的设计理念 → FLOW 的"事实库"（facts.yaml）就是这种思路的事实层
  - ② Beancount 的"重写账本不留旧版本" 与 FLOW "D040/D047 决策编号 + 旧版本保留"形成对比：FLOW 选了"重决策保留多版本"，适合 B 端审批场景
  - ③ 可学习 Fava 的 "多视图切换" UI 模式

## 三、横向对比

| 项目 | 核心场景 | 杜邦支持 | AI 能力 | 部署形态 | 商业化 |
| --- | --- | --- | --- | --- | --- |
| OpenBB Terminal | 二级市场研究 | 部分（/fa） | 中（Q&A） | 本地 + 云 | 双轨 |
| FinGPT | 文本理解 | 无 | 强（LLM） | 本地 | 无 |
| FinRL | 量化交易 | 无 | 强（RL） | 本地 | 无 |
| FinanceToolkit | 比率库 | 部分（ratios） | 无 | 库 | 无 |
| QuantStats | 组合绩效 | 无 | 无 | 库 | 无 |
| Beancount 等 | 个人记账 | 无 | 无 | 本地 | 无 |

## 四、对 FLOW 的核心启发

1. **指标体系是核心竞争力**：FinanceToolkit 的 150+ 比率对照表可作 FLOW 指标字典 v2 的扩展示例。但 FLOW 的 167 科目 + 通用 + 物流行业指标体系已覆盖经营分析核心。
2. **"自然语言问数" 是 AI 财分差异化方向**：OpenBB 已经在做。FLOW 当前没有 Q&A，可以考虑加一个"指标问答"接口：用户问"顺丰的净利率为什么下降？"，系统从事实库 + 跨公司对标生成自然语言回答。
3. **报告自动生成的范式**：OpenBB Workspace / QuantStats 都是"指标 + 自动图 + 一键 HTML/PDF"。FLOW 的 `docs/library/index.html` 已经做到了，但目前是单页静态长滚动；可以补"按公司、按期间生成独立 PDF/HTML 报告"的能力。
4. **纯文本账本模式**：Beancount 等的"文本即账本"思路，与 FLOW 的"facts.yaml 即账本"一致，强化了"事实库是底层"的判断。

## 五、差异化机会（FLOW 可以做但竞品不做）

- **B 端私有部署 + 中文会计准则 + 中国财报表披露**：OpenBB / FinGPT 都是面向全球资本市场，不专门做中国 A 股 / 港股 + 中文报表 + 中文会计科目
- **杜邦拆解 + 同业对标 + 行业标杆**：OpenBB 的杜邦浅尝辄止；FLOW 已经在做"五家公司作为代理样本" 的同业对比，且把杜邦拆到五因子 + 二级子项
- **指标体系版本化（v0/v1/v2 评审集）**：FinanceToolkit 只有一个静态库；FLOW 把指标体系当作"数据集"管理（v0-draft → v1-effective → v2-candidate），有 D040/D047 等决策编号
- **从抽报到覆盖矩阵的全链路**：反向解析财报 → 抽取事实 → 抽到事实库 → 算指标 → 算覆盖 → 暴露缺口。这是 FLOW 独有的 "P5 反向解析" 流程，OpenBB 不做