# 指标权威口径核查档案（EVA 央企口径 / CCC 标准定义）

- 归档日期：2026-09-12
- 采集方式：公开网络检索（WebSearch，官方/权威源优先）
- 用途：内部指标库 v1.1 新增条目（eva、sgr、roic、ccc_days、ocf 系）的口径依据
- 性质：原始研究档案，不可变；修正以新增文件完成

## 1. EVA 经济增加值（国资委央企考核口径）

- **权威定义**（司法部官网收录《中央企业负责人经营业绩考核暂行办法》）：经济增加值 = 税后净营业利润（NOPAT）− 调整后资本 × 平均资本成本率。
- **NOPAT**：净利润 +（利息支出 + 研究开发费用调整项）×（1 − 所得税率）；调整项含非经常性收益、无息流动负债等。
- **资本成本率**：央企原则上 **5.5%**；军工等资产通用性差的企业 **4.1%**；资产负债率超标的工业企业（75%+）/非工业企业（90%+）上浮 0.5 个百分点。
- **2019 政策要点**：研发投入（费用化口径）视同利润加回，引导研发投入稳定增长。
- 理论起源：Stern Stewart「剩余收益」思想。

来源：
- 《中央企业负责人经营业绩考核暂行办法》（2009 修正本），司法部官网：https://www.moj.gov.cn/pub/sfbgw/flfggz/flfggzbmgz/201004/t20100428_144810.html
- 湖南省国资委「国资委业绩考核中 EVA 是什么」：https://gzw.hunan.gov.cn/gzw/zxts/cjwt/201512/t20151223_2284936.html
- 国资委《关于以经济增加值为核心加强中央企业价值管理的指导意见》（国资委官网）

## 2. 现金周转周期 CCC（CFA/CFI 标准定义）

- **标准公式**：CCC = DIO + DSO − DPO；CFA 课程中亦称「净营业周期」（net operating cycle，与联合资信附件中文名一致）。
- 分量口径：DIO =（平均存货 ÷ 营业成本）× 365；DSO =（平均应收账款 ÷ 营业收入）× 365；DPO =（平均应付账款 ÷ 营业成本）× 365。
- **解读**：CCC 越低营运资金效率越高；负值 = 先收客户现金后付供应商（强议价/类平台模式）；上升 = 现金被营运循环占用。

来源：
- Corporate Finance Institute「Cash Conversion Cycle」：https://corporatefinanceinstitute.com/resources/accounting/cash-conversion-cycle/
- CFA Institute（Inside Investing，净营业周期表述）：https://blogs.cfainstitute.org/insideinvesting/2013/05/21/a-look-at-the-cash-conversion-cycle/
- J.P. Morgan Treasury（营运资金视角分量公式）：https://www.jpmorgan.com/insights/treasury/receivables/understanding-and-optimizing-your-cash-conversion-cycle

## 3. 对指标库 v1.1 的落地

- `eva` 条目公式文本与 caliber 直接采用国资委口径（含 5.5%/4.1% 与研发加回）；benchmark 保留「不得仅凭 EVA 单独下结论」警告。
- `ccc_days` 条目采用 CFA 标准定义 + 联合资信「净营业周期」同族标注；分量复用库内既有 dio/dso/dpo 天数条目（依赖边）。
- `sgr`（Higgins 经典口径）、`roic`（NOPAT 口径）沿用教科书定义并标注口径分歧。
