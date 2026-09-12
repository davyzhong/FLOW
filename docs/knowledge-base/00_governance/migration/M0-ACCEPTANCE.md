# M0 验收记录（Task 2 / 批次 M0）

验收日期：2026-09-12。执行：ZCode 会话（用户指派 M0+M1 修复车道）。checkpoint：`7567e0a`（执行批次开始时解析的 origin/main HEAD，批次内不漂移）。

## 修复内容（相对 GPT 初版 2016306/dd5a24b/7567e0a 的差异）

1. **基线自包含漂移修复**：初版基线（dd5a24b，checkpoint 2016306）与重定义基线（7567e0a 提交内的版本）均以工作树模式生成，混入未提交内容（实证：TAXONOMY 字节 1350 vs tree 1349、source-register consumer_count 2 vs 1），`--check` 不可重放。本版以 `inventory.py --tree-ish 7567e0a`（git ls-tree/cat-file，blob 级）重新生成全部四件产物，`--check` PASS。
2. **不可变锁字节不变**：immutable-paths.lock.tsv 哈希 `9caf15ec…` 与初版一致——五个不可变根的逐文件哈希在全部迁移提交中未被触碰。
3. **来源级基线建立（Step 5c）**：原 15:46 截面在 vault git 无精确快照，经用户批准改用可复现 tree `ada825ce`（16:17:36），逐条登记 **3317** 条（=3035 声明 + 282 批准订正，记录于 source-inputs.yaml）：微信 1630 / 财务 285 / 企管 453 / 物流 125 / wiki 关键词 824。每条含 locator、标题、作者、K1–K8 程序路由（3061 条命中）、重复组（18 条）、availability；`source_baseline.py check` PASS（文件哈希对账 + 结构 + 排序 + 唯一性）。
4. **path-map 补齐**：新增 100 行 M1+ canonical 产物登记（keep），可变 Markdown 处置覆盖 433/433。
5. **external-consumers.tsv**：登记 vault 知识地图、agent memory、davybase 回链、外部深链 4 类仓库扫描不可见消费者，全部 keep/compatibility。

## 计数与哈希

| 项 | 值 |
|---|---|
| checkpoint tree | `7567e0a` |
| baseline.yaml | 见 migration/baseline.yaml（inventory/consumer/storage/lock 四件哈希） |
| source-baseline 条数 | 3317（locator-only，vault tree ada825ce 指纹） |
| consumer-registry 行数 | 634（提交时以文件为准） |
| 脚本测试 | 52/52 PASS（unittest discover scripts/tests） |

## 用户签项记录

- 车道决策（2026-09-12）：ZCode 执行 M0+M1 修复，GPT 暂停待 M1 验收后接 M2。
- 截面订正批准（2026-09-12）：15:46 → 16:17:36（tree ada825ce），count 3035 → 3317。

## 例外与边界

- GPT 会话在途的 `scripts/documentation/knowledge_release.py` 未提交修改未纳入本批（Task 8 属 M2 车道，待其对齐逐条基线后另行验收）。
- GPT 已提交的组级 coverage（063b9ea）与逐条基线的对齐属 M2 修复项，不在 M0 范围。
