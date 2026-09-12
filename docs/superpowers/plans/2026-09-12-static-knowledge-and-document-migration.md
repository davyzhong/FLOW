# FLOW Documentation and Static Knowledge Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改写原始档案、不改变产品合同和业务代码语义的前提下，把 FLOW 迁移为可校验、可回放、可独立于 Obsidian 使用的静态知识库与有唯一当前入口的项目文档体系。

**Architecture:** 迁移按 M0–M6 七个独立批准批次推进：先建立清单和不可变基线，再建立治理工具与目录骨架，随后发布静态知识版本，最后统一产品/规格/计划、整理历史并执行无上下文接续验收。所有移动都由消费者清单驱动；状态通过元数据和索引表达，发布内容通过版本化文件、release lock 与 SHA-256 固定。

**Tech Stack:** Markdown、YAML、TSV、JSON Schema Draft 2020-12、Python 3.13、PyYAML、jsonschema、`unittest`、Git、GitHub Actions。

---

## 计划元数据

| 字段 | 值 |
|---|---|
| Plan ID | FLOW-DOC-MIGRATION-001 |
| 状态 | draft；尚未授权执行 |
| 版本 | 1.1 |
| 建立日期 | 2026-09-12 |
| 设计依据 | `docs/superpowers/specs/2026-09-12-static-knowledge-and-document-architecture-design.md` **V1.1** |
| 来源基线 | `obsidian-2026-09-12T15:46+08:00` |
| 目标知识发布 | `flow-knowledge-2026-09-12.1` |
| 编写基线 | Git `05f614b`（设计 V1.1）；执行每一批前必须重新盘点 |
| 决策依据 | D049、D051 |

**V1.1 修订记录（2026-09-12）**：同步设计 V1.1——(1) Task 15 接续测试十题降为五题（第 1/2/4 题 critical，通过线 4/5）；(2) Task 6/8 验收从写死 3035 改为 M0 基线清单哈希对账；(3) Task 3/7 的 JSON Schema 优先路径收敛为 `scripts/documentation/check_docs.py` 单一检查入口，Schema 文件后置为可选增强；(4) Task 2 补 M0 二进制存储分级盘点（设计 §4.9）；(5) Task 8 补 release 批量切换工具；(6) Task 12 补顶层 HANDOFF/会话归档归宿；(7) §0 补角色门禁映射引用。

## 0. 执行授权与停止规则

本文件是实施计划，不是实施授权。执行者必须逐批取得 M0、M1、M2、M3、M4、M5、M6 的明确批准；批准一个批次不自动批准下一个批次。M0–M6 均不得借文档迁移改变产品功能、财务公式、数据合同、权限边界或程序行为。

批次内的门禁按设计规范 §4.6.1 分两类执行：**AI 可自验项**（schema/链接/哈希/来源核验）失败即阻断当前步骤；**必须用户签项**（批次批准、`CURRENT_RELEASE` 切换、决策 accepted、删除类操作、安装依赖、创建 Release）由 AI 准备变更后停下等用户确认，不得代签。

执行任一任务前：

1. 使用独立 `codex/` 工作树或用户明确指定的隔离环境；
2. 读取 `docs/knowledge-base/README.md`、`AGENT_START_HERE.md`、`PROJECT_STATE.md`、设计规范和本计划；
3. 检查 `git status --short`，不覆盖、暂存或提交其他任务的在途改动；
4. 记录当前提交、远端状态、不可变基线和机器消费者；
5. 只暂存当前任务文件，验证后提交并推送 `origin`；
6. 若不可变哈希变化、规范入口重复、消费者失败或知识覆盖不能闭合，立即停止当前批次。

以下目录永久原位：

- `docs/knowledge-base/01_conversations/raw/`；
- `docs/knowledge-base/02_research/original/`；
- `docs/knowledge-base/03_assets/logistics_daily/`；
- `docs/knowledge-base/03_assets/external_reference/`；
- `docs/knowledge-base/05_design/approved/`。

## 1. 文件与职责总图

### 1.1 新增工具

| 文件 | 单一职责 |
|---|---|
| `scripts/documentation/__init__.py` | 文档治理工具包边界 |
| `scripts/documentation/inventory.py` | 生成文档、消费者和不可变文件清单 |
| `scripts/documentation/metadata.py` | 读取 frontmatter，执行 doc ID、状态与引用校验 |
| `scripts/documentation/links.py` | 检查 Markdown 相对链接、兼容入口和 allowlist |
| `scripts/documentation/knowledge_release.py` | 生成并验证 coverage、release lock 和发布哈希 |
| `scripts/documentation/reader_rubric.py` | 校验 M6 固定题集、rubric 和评分记录 |
| `scripts/documentation/check_docs.py` | 统一检查入口：聚合 metadata/links/inventory/release 校验（设计 V1.1 §6.3），供 `make docs-check` 与 CI 调用 |
| `scripts/tests/test_document_inventory.py` | M0 清单与不可变基线测试 |
| `scripts/tests/test_document_metadata.py` | M1 元数据与跨文档状态测试 |
| `scripts/tests/test_document_links.py` | M5/M6 链接和兼容入口测试 |
| `scripts/tests/test_knowledge_release.py` | M2 静态知识发布测试 |
| `scripts/tests/test_reader_rubric.py` | M6 读者测试记录测试 |

### 1.2 新增治理与发布文件

| 文件 | 单一职责 |
|---|---|
| `docs/knowledge-base/00_governance/IMMUTABLE_PATHS.md` | 人类可读的不可变档案政策 |
| `docs/knowledge-base/00_governance/immutable-paths.lock.tsv` | M0 固定路径、逐文件哈希和基线归属 |
| `docs/knowledge-base/00_governance/migration/document-inventory.tsv` | 全量文档类型、状态、权威和目标处置 |
| `docs/knowledge-base/00_governance/migration/storage-inventory.tsv` | M0 二进制体积分布与 A/B/C/D 存储分级标注（设计 §4.9） |
| `docs/knowledge-base/00_governance/migration/consumer-registry.tsv` | 代码、测试、配置、脚本和文档消费者 |
| `docs/knowledge-base/00_governance/migration/path-map.tsv` | 旧路径、新路径、兼容策略和批准状态 |
| `docs/knowledge-base/00_governance/migration/baseline.yaml` | M0 提交、计数和清单哈希 |
| `docs/knowledge-base/00_governance/releases/release-lock.schema.json` | 静态发布锁合同（机器合同，保留；元数据 schema 已收敛为 check_docs.py 内置校验，见设计 V1.1 §6.3） |
| `docs/knowledge-base/00_governance/releases/CURRENT_RELEASE` | 当前静态知识 release ID |
| `docs/knowledge-base/00_governance/releases/flow-knowledge-2026-09-12.1/*` | 首版发布说明、coverage、lock 和哈希 |

### 1.3 当前入口与目标目录

稳定入口最终为：

- `docs/README.md`；
- `docs/00_start_here/README.md`；
- `docs/00_start_here/PROJECT_STATE.md`；
- `docs/00_start_here/READING_ORDER.md`；
- `docs/00_start_here/DOCUMENT_MAP.md`；
- `docs/50_plans/CURRENT_ROADMAP.md`；
- `docs/10_governance/DECISION_INDEX.md`；
- `docs/20_product/PRODUCT_VISION.md`；
- `docs/20_product/PRODUCT_SCOPE.md`。

`docs/knowledge-base/00_start_here/*`、`docs/superpowers/plans/*` 和 `docs/knowledge-base/04_decisions/DECISION_LOG.md` 在切换后保留兼容入口或历史原件，不形成第二份当前事实。

### 1.4 明确不移动的机器数据路径

以下路径虽位于旧文档树，但当前被程序、测试或生成器直接消费，M3/M5 默认原位保留：

- `docs/implementation/p5/*.yaml` 与 `*.html`；
- `docs/implementation/objective-analysis/metric-execution-coverage.md`；
- `docs/knowledge-base/02_research/synthesis/指标库初始数据集_v0_草案.yaml`；
- `docs/knowledge-base/02_research/synthesis/会计基础数据集_v0_草案.yaml`；
- `docs/superpowers/specs/financial-facts-contract.md`；
- `docs/knowledge-base/02_research/original/p5_samples/`。

只有消费者清单归零并满足两个正式发布周期验证后，才另立计划讨论移动。

## 2. 批次依赖

```text
M0 全量清单与冻结
 └─ M1 治理工具与稳定入口
     └─ M2 静态知识 v1
         ├─ M3 产品、架构与规格统一
         │   └─ M4 唯一路线图与工作包
         │       └─ M5 历史整理与兼容收口
         └──────────────────────────────┐
                                        └─ M6 全面验证与接续测试
```

M2 和 M3 不可并行，因为 M3 正式文档必须引用可解析的知识发布。M5 不能早于 M4，否则历史计划和当前工作包尚未分离。M6 只验证已完成迁移，不代替任何前置批次的内容审查。

---

### Task 1: M0.1 建立可重复的文档清单工具

**Files:**
- Create: `scripts/documentation/__init__.py`
- Create: `scripts/documentation/inventory.py`
- Create: `scripts/tests/test_document_inventory.py`

- [ ] **Step 1: 写失败测试，固定扫描边界**

测试必须证明：Git 跟踪文件为主清单；`.git`、缓存、构建产物不进入；raw/original 会被识别为 immutable；每行至少包含 `path`、`kind`、`mutability`、`consumer_count`、`sha256`。

```python
def test_inventory_marks_raw_and_original_as_immutable(tmp_path: Path) -> None:
    rows = build_inventory(FIXTURE_ROOT)
    immutable = {row.path for row in rows if row.mutability == "immutable"}
    assert "docs/knowledge-base/01_conversations/raw/a.md" in immutable
    assert "docs/knowledge-base/02_research/original/b.md" in immutable
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m unittest scripts.tests.test_document_inventory -v`
Expected: FAIL，提示 `scripts.documentation.inventory` 不存在。

- [ ] **Step 3: 实现最小扫描器**

`inventory.py` 使用 `git ls-files -z` 获取受控文件，使用 `pathlib` 和 `hashlib.sha256`；禁止跟随目录外符号链接。分类规则与不可变根路径定义为具名常量，不把路径散落在测试中。

- [ ] **Step 4: 增加消费者识别**

扫描非 raw/original 文本文件中的 `docs/` 路径字面量，记录消费者文件、行号、消费者类型和是否可同步。二进制文件只记录哈希，不尝试解码。

- [ ] **Step 5: 运行定向测试**

Run: `python3 -m unittest scripts.tests.test_document_inventory -v`
Expected: PASS，且 fixture 的路径、哈希和消费者数量稳定。

- [ ] **Step 6: 提交并推送**

```bash
git add scripts/documentation/__init__.py scripts/documentation/inventory.py \
  scripts/tests/test_document_inventory.py
git commit -m "docs(tooling): add documentation inventory scanner"
git push origin HEAD
```

### Task 2: M0.2 生成迁移基线、不可变锁和消费者登记

**Files:**
- Create: `docs/knowledge-base/00_governance/IMMUTABLE_PATHS.md`
- Create: `docs/knowledge-base/00_governance/immutable-paths.lock.tsv`
- Create: `docs/knowledge-base/00_governance/migration/document-inventory.tsv`
- Create: `docs/knowledge-base/00_governance/migration/consumer-registry.tsv`
- Create: `docs/knowledge-base/00_governance/migration/path-map.tsv`
- Create: `docs/knowledge-base/00_governance/migration/baseline.yaml`
- Modify: `docs/knowledge-base/README.md`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`

- [ ] **Step 1: 在干净隔离工作树记录检查点**

Run: `git status --short && git rev-parse HEAD && git rev-parse origin/main`
Expected: 当前任务工作树无无关改动；两个提交可明确记录。若不干净，停止而不是清理他人文件。

- [ ] **Step 2: 生成只读候选清单**

Run: `python3 scripts/documentation/inventory.py --repo . --output-dir /tmp/flow-doc-m0`
Expected: 生成 inventory、consumer registry、immutable lock 和 baseline；命令不修改仓库。

- [ ] **Step 3: 人工审阅不可变根和消费者**

至少逐项确认 `raw`、`original`、两个原图目录和 `05_design/approved`；确认当前已知的 P5 YAML、coverage 文档、事实合同、原始财报样本及其程序消费者全部出现。

- [ ] **Step 4: 写入批准后的基线文件**

Run: `python3 scripts/documentation/inventory.py --repo . --output-dir docs/knowledge-base/00_governance/migration --write-lock docs/knowledge-base/00_governance/immutable-paths.lock.tsv`
Expected: 输出按 UTF-8 路径排序；`baseline.yaml` 保存当前提交、文件数、逐清单哈希和生成器版本。

- [ ] **Step 5: 建立完整 `path-map.tsv`**

每个可变 Markdown 都必须有 `keep`、`move`、`rewrite`、`archive` 或 `compatibility` 处置；所有机器消费者路径默认 `keep`，不得留空。M0 只登记，不移动。

- [ ] **Step 5b: 生成二进制存储分级清单**

`inventory.py` 按 `size`、`extension` 和目录特征为全部二进制（png/jpg/pdf/html 单体/zip/jsonl 等）生成 `storage-inventory.tsv`，每行含 `path`、`size`、`sha256`、`proposed_tier`（A git / B lfs / C release / D redundant-candidate，判定顺序 D→C→B→A，规则见设计 §4.9）。已知量级参考（2026-09-12 盘点）：知识库图片约 1544 张 / 268MB，`02_research/original` 含 8–23MB PDF 年报，`01_conversations/raw` 含 22MB jsonl——proposed_tier 仅登记建议，B/C/D 的实际处置独立成批并单独批准，本步骤不移动任何文件。重复候选（D）必须先与库内其他文件 SHA-256 对账确认。

- [ ] **Step 6: 验证基线可重复**

Run: `python3 scripts/documentation/inventory.py --repo . --check docs/knowledge-base/00_governance/migration/baseline.yaml`
Expected: PASS；第二次生成与首次字节一致。

- [ ] **Step 7: 重建知识库 manifest**

使用现有 manifest 规则生成 `inventory.tsv` 与 `sha256sums.txt`，明确排除这两个清单自身；再运行：

Run: `git diff --check && python3 -m unittest scripts.tests.test_document_inventory -v`
Expected: PASS；旧不可变文件哈希全部保持不变。

- [ ] **Step 8: 提交、推送并等待 M0 验收**

Commit: `docs(migration): freeze M0 documentation baseline`。
M0 验收记录必须包含提交、计数、baseline hash、消费者数量和例外；未获得 M1 批准前停止。

---

### Task 3: M1.1 建立文档元数据校验器与统一检查入口

**Files:**
- Create: `docs/10_governance/legacy-exemptions.tsv`
- Create: `scripts/documentation/metadata.py`
- Create: `scripts/documentation/check_docs.py`
- Create: `scripts/tests/test_document_metadata.py`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 写状态与引用失败测试**

覆盖：重复 `doc_id`；plan 引用未 approved spec；canonical 文档引用不存在 release；非法状态转换；`PROJECT_STATE` current 重复；legacy-exempt 修改后仍绕过校验。

- [ ] **Step 2: 运行失败测试**

Run: `cd services/api && uv run python ../../scripts/tests/test_document_metadata.py -v`
Expected: FAIL，校验模块不存在。

- [ ] **Step 3: 以纯 Python 实现元数据合同校验（设计 V1.1 §6.3）**

按 doc_type 在 `metadata.py` 内实现必填字段、状态枚举与七项跨文档检查（ID 唯一 / 引用存在 / 上游状态 / release 可解析 / 状态转换合法 / canonical 有来源 / 工作包不绕过 approved spec），不引入 `jsonschema` 依赖、不新建 schema.json 文件；`document-metadata.schema.json` 与 `knowledge-artifact.schema.json` 后置为可选增强，仅当出现纯 Python 校验无法表达的复杂约束时另行立项。`check_docs.py` 作为统一 CLI 入口聚合调用。

- [ ] **Step 4: 实现跨文档完整性校验与历史豁免**

历史豁免只允许 `legacy-exemptions.tsv` 中 M0 已登记且未实质修改的文件；豁免名单外的任何正式文档（新增或修订）必须通过全部检查。

- [ ] **Step 5: 接入现有 static-python job**

不新增第 17 个 CI job，避免破坏 `test_ci_gate_inventory.py` 的 16 门禁合同。把现有系统 Python 的脚本测试改为在 API 的锁定开发环境中运行（PyYAML 由既有环境提供），再增加元数据检查：

```bash
cd services/api
uv run python -m unittest discover -s ../../scripts/tests -v
uv run python ../../scripts/documentation/check_docs.py --check
```

Expected: 当前迁移阶段仅校验新/修改正式文档和唯一入口，历史豁免有明确报告；原有脚本测试仍全部执行。

- [ ] **Step 6: 运行验证**

```bash
cd services/api
uv run python ../../scripts/tests/test_document_metadata.py -v
uv run ruff check ../../scripts/documentation ../../scripts/tests
uv run python ../../scripts/documentation/check_docs.py --check
```

Expected: 全部 PASS。

- [ ] **Step 7: 提交并推送**

Commit: `docs(governance): enforce document metadata contracts`。

### Task 4: M1.2 建立目标目录骨架与唯一接续入口

**Files:**
- Create: `docs/00_start_here/README.md`
- Create: `docs/00_start_here/PROJECT_STATE.md`
- Create: `docs/00_start_here/READING_ORDER.md`
- Create: `docs/00_start_here/DOCUMENT_MAP.md`
- Create: `docs/10_governance/README.md`
- Create: `docs/20_product/README.md`
- Create: `docs/30_architecture/README.md`
- Create: `docs/40_specs/README.md`
- Create: `docs/50_plans/README.md`
- Create: `docs/60_delivery/README.md`
- Create: `docs/70_operations/README.md`
- Create: `docs/80_reviews/README.md`
- Create: `docs/90_archive/README.md`
- Modify: `docs/README.md`
- Modify: `docs/knowledge-base/00_start_here/PROJECT_STATE.md`
- Modify: `docs/knowledge-base/00_start_here/AGENT_START_HERE.md`
- Modify: `docs/knowledge-base/README.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 为唯一 current state 写失败测试**

在 `test_document_metadata.py` 增加断言：全仓恰有一个 `doc_type: state`、身份 `PROJECT_STATE`、`status: current`；旧路径可存在，但不能是第二个 current state。

- [ ] **Step 2: 创建目标目录 README**

每个 README 只说明职责、权威入口、允许 doc_type 和禁止内容，不复制状态、产品规格或路线图正文。

- [ ] **Step 3: 建立新 `PROJECT_STATE.md`**

从执行时最新代码、迁移头、CI 和已提交证据重新核对后写入；不能照搬 2026-09-12 历史瞬时状态。旧 `knowledge-base/00_start_here/PROJECT_STATE.md` 改成兼容导航，保留历史 Git 可追溯性但移除 current 身份。

- [ ] **Step 4: 建立五文档最短阅读顺序**

`READING_ORDER.md` 必须保证新 Agent 最多读取五份文档即可定位：产品范围、当前状态、事实合同、决策、当前路线图/过渡计划和知识发布。M4 前路线图位置仍指向 `2026-09-07-unified-next-plan.md`，不得提前声称 `CURRENT_ROADMAP.md` 已生效。

- [ ] **Step 5: 更新仓库入口**

更新 `AGENTS.md`、`docs/README.md` 和知识库导航到新起点；`DOCUMENT_MAP.md` 记录旧→新，不修改 raw/original 中的旧链接。

- [ ] **Step 6: 验证唯一入口**

Run: `cd services/api && uv run python ../../scripts/documentation/metadata.py --check`
Expected: 一个 current state；README 无复制的任务状态；所有新入口可达。

- [ ] **Step 7: 提交并推送**

Commit: `docs(structure): establish canonical documentation entrypoints`。

### Task 5: M1.3 建立决策索引和治理规则

**Files:**
- Create: `docs/10_governance/DOCUMENT_GOVERNANCE.md`
- Create: `docs/10_governance/KNOWLEDGE_GOVERNANCE.md`
- Create: `docs/10_governance/TERMS_AND_NAMESPACES.md`
- Create: `docs/10_governance/DECISION_INDEX.md`
- Create: `docs/10_governance/decisions/D001--product-not-dashboard.md` through `D051--obsidian-knowledge-gate.md`
- Modify: `docs/knowledge-base/04_decisions/DECISION_LOG.md`
- Modify: `docs/knowledge-base/04_decisions/CHANGE_IMPACT_MAP.md`
- Modify: `docs/2026-09-07-documentation-governance.md`
- Modify: `docs/00_start_here/DOCUMENT_MAP.md`

- [ ] **Step 1: 写决策完整性测试**

测试 51 个 D 编号不缺失、不重复；`DECISION_INDEX.md` 每项指向存在文件；accepted/amended/superseded 关系可解析；旧日志仍可作为历史来源访问。

- [ ] **Step 2: 逐项拆分，不改写决定**

每个 D 文件保存原决定、原因和历史状态，新增标准元数据、`source_refs`、`amends`/`supersedes`。对“有效但被较晚方向收窄”的决定，不擅自改为 rejected；用影响关系表达适用范围。

- [ ] **Step 3: 将旧日志改为兼容索引**

保留开头的历史说明和 Git 历史入口，正文链接 `DECISION_INDEX.md`；若迁移会让不可变会话中的旧路径失效，则旧路径永久保留。

- [ ] **Step 4: 固化命名空间**

在 `TERMS_AND_NAMESPACES.md` 区分 K1–K8、L1–L4、D、U、O 与历史 Phase/WS/M/P；具体任务状态仍不得写入该长期治理文档。

- [ ] **Step 5: 运行完整性与链接验证**

Expected: D001–D051 全覆盖；无重复当前决策源；旧链接有兼容入口。

- [ ] **Step 6: 提交、推送并等待 M1 验收**

Commit: `docs(governance): normalize decisions and documentation policy`。
M1 验收后才申请 M2；此时尚未发布 `flow-knowledge-2026-09-12.1`。

---

### Task 6: M2.1 建立来源覆盖与来源登记

**Files:**
- Create: `docs/knowledge-base/10_sources/README.md`
- Create: `docs/knowledge-base/10_sources/SOURCE_REGISTER.md`
- Create: `docs/knowledge-base/10_sources/source-register.tsv`
- Create: `docs/knowledge-base/10_sources/snapshots/obsidian-2026-09-12T15-46+08-00.yaml`
- Create: `docs/knowledge-base/00_governance/releases/flow-knowledge-2026-09-12.1/coverage.tsv`
- Create: `scripts/documentation/knowledge_release.py`
- Create: `scripts/tests/test_knowledge_release.py`

- [ ] **Step 1: 写来源覆盖失败测试（基线对账，设计 V1.1 §10.1）**

测试必须检查 `source_id` 唯一、条目集合与 M0 冻结的来源基线清单一一对应（数量由基线清单定义，**不写死篇数数字**）、固定 snapshot ID、内容指纹、处置、K1–K8 路由、敏感等级和来源定位符；不得把“程序关键词命中”当成人工 verified。基线冻结与发布之间的已登记差异必须以 `added`/`withdrawn` delta 说明。

- [ ] **Step 2: 定义来源身份规则**

首选仓库内相对路径；无法存全文时使用固定 vault 相对路径、标题、作者、截面、文件字节数和允许保存的 SHA-256。重复转载保留独立 source ID，并通过 `duplicate_group_id` 聚合，不能删除以凑数。

- [ ] **Step 3: 从现有静态材料重建覆盖**

输入仅限仓库已有的 A/B/C/D、W1–W4 扫描评估、`08_wechat_sources` 移交内容、既有 original/synthesis 和来源目录；不重新动态扫描 Obsidian。若基线清单条目无法一一恢复稳定定位符，M2 停止并报告缺口，不伪造记录。

- [ ] **Step 4: 区分处置与核验**

`disposition` 只允许 adopted、partially-adopted、duplicate、background、rejected、pending-verification；`verification` 单独记录 program-routed、representative-read、human-verified。敏感性只放 `sensitivity`。

- [ ] **Step 5: 运行确定性测试**

Run: `cd services/api && uv run python ../../scripts/tests/test_knowledge_release.py -v`
Expected: coverage 与 M0 基线清单一一对应（哈希对账通过）、唯一、排序稳定；两次生成哈希一致。

- [ ] **Step 6: 提交来源层**

Commit: `docs(knowledge): establish fixed source coverage`。
此提交不创建 `CURRENT_RELEASE`，因为知识资产尚未完成。

### Task 7: M2.2 建立知识资产校验、taxonomy 和作者批次

**Files:**
- Create: `docs/knowledge-base/20_knowledge_cards/README.md`
- Create: `docs/knowledge-base/20_knowledge_cards/TAXONOMY--v1.0.yaml`
- Create: `docs/knowledge-base/20_knowledge_cards/authoring-batches.tsv`
- Create: `docs/knowledge-base/20_knowledge_cards/{finance,operations,methods,governance,technology}/*.md`
- Create: `docs/knowledge-base/30_domain_handbooks/*/README--v1.0.md`
- Create: `docs/knowledge-base/40_methods_and_patterns/README.md`
- Create: `docs/knowledge-base/50_product_mappings/README.md`
- Create: `docs/knowledge-base/50_product_mappings/FLOW-PRODUCT-MAPPING--v1.0.md`

- [ ] **Step 1: 写知识资产校验失败测试（纯 Python，设计 V1.1 §6.3）**

覆盖 knowledge-card、domain-handbook、taxonomy、product-mapping 四类资产的必填字段与状态枚举（校验逻辑并入 `metadata.py`/`check_docs.py`，不新建 schema.json）；canonical 资产必须有稳定 ID、版本、来源、权威、敏感性和 release；source 引用不能形成无源闭环。

- [ ] **Step 2: 建立 taxonomy**

将 K1–K8 映射到设计规定的 11 个领域手册，明确一主域、多标签、同义词和拒绝标签；taxonomy 是分类，不批准产品功能。

- [ ] **Step 3: 生成 `authoring-batches.tsv`**

按“来源簇→候选知识 ID→主领域→复核人→冲突状态→目标版本”拆批。每批最多 25 张知识卡；同主题转载先聚类再形成一张卡，多来源共同挂接。

- [ ] **Step 4: 逐批编写知识卡**

每张卡固定包含定义、业务目的、输入、规则、适用/不适用条件、常见误用、来源与核验、FLOW 影响。文章示例阈值、模板值和企业内部值不能成为 FLOW 默认值。

- [ ] **Step 5: 每批执行双层复核**

第一层检查来源和准确转述；第二层检查财务/经营含义、冲突和权限。未通过者保持 candidate/verified，不进入首版 canonical lock。

- [ ] **Step 6: 编写 11 个领域手册**

领域为 financial statements、financial analysis、revenue and growth、cost and expense、profitability、cash and working capital、budget and forecast、operational efficiency、logistics and supply chain、management reporting、finance AI governance。每本手册必须回答边界、指标、维度、比较/下钻、L1–L4、典型路径、误用和产品映射。

- [ ] **Step 7: 建立产品映射**

逐项记录知识资产→FLOW 对象→当前能力→L1–L4→采用/试点/后置/拒绝→缺口→决策/规格。没有产品映射的知识可以留在知识库，但不能直接进入规格或计划。

- [ ] **Step 8: 运行每批校验并提交**

Run: `cd services/api && uv run python ../../scripts/documentation/metadata.py --check-knowledge`
Expected: 当前批 schema、source_refs 和 ID 全部通过。

每个作者批次单独提交并推送，提交信息为 `docs(knowledge): add <domain> knowledge batch <n>`；不得把全部内容压成一个不可审阅提交。

### Task 8: M2.3 构建并发布首个静态知识版本

**Files:**
- Create: `docs/knowledge-base/00_governance/releases/release-lock.schema.json`
- Create: `docs/knowledge-base/00_governance/releases/flow-knowledge-2026-09-12.1/release.yaml`
- Create: `docs/knowledge-base/00_governance/releases/flow-knowledge-2026-09-12.1/release-lock.yaml`
- Create: `docs/knowledge-base/00_governance/releases/flow-knowledge-2026-09-12.1/sha256sums.txt`
- Create: `docs/knowledge-base/00_governance/releases/CURRENT_RELEASE`
- Modify: `docs/knowledge-base/README.md`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 写发布失败测试**

覆盖：资产漏锁、路径不存在、哈希不符、非 canonical 入锁、coverage 与 M0 基线不符、source 引用失效、旧 release 不可恢复、先切 `CURRENT_RELEASE`。

- [ ] **Step 2: 实现 release builder**

`knowledge_release.py build` 从批准的 canonical 资产生成 lock；lock 必须枚举 knowledge-card、domain-handbook、taxonomy、product-mapping、source-register、coverage 的 ID、类型、版本、路径、SHA-256 和上游关系。

- [ ] **Step 3: 生成候选发布，不切 current**

Run: `cd services/api && uv run python ../../scripts/documentation/knowledge_release.py build --release flow-knowledge-2026-09-12.1 --check-only`
Expected: PASS，并给出确定性的候选 lock 摘要。

- [ ] **Step 4: 独立复核 coverage 和敏感信息**

抽样覆盖每个 K 域、每种权威等级、每种处置和所有 authorized-internal/restricted 条目；确认仓库未复制未授权原文、内部数值或文件。

- [ ] **Step 5: 写入发布文件并验证旧基线**

生成 `release.yaml`、`release-lock.yaml` 和发布 `sha256sums.txt`；重跑 M0 immutable lock，必须证明所有基线文件字节未变。

- [ ] **Step 6: 提交尚未切 current 的发布内容**

提交 `release.yaml`、`release-lock.yaml`、coverage、知识资产版本和发布哈希：

Commit: `docs(knowledge): prepare flow knowledge 2026-09-12.1`。

- [ ] **Step 7: 提供 release 批量切换工具并最后切换 `CURRENT_RELEASE`**

`knowledge_release.py` 增加 `switch` 子命令（设计 V1.1 §4.8）：把全部引用旧 release 的文档元数据一次更新为新 release ID，随即运行 `check_docs.py` 全量验证，输出切换前后 doc 清单与逐文件 diff 作为验证记录。只有前六步通过后，才用该工具执行首次切换（`pre-static-*` → `flow-knowledge-2026-09-12.1`）：`CURRENT_RELEASE` 写入与元数据批量更新作为同一独立提交。CI 增加 `knowledge_release.py verify --current`，仍放入 static-python job。

- [ ] **Step 8: 重建知识库总 manifest**

总 manifest 不进入自己的哈希计算；验证 release lock 与归档 manifest 的职责不混淆。

- [ ] **Step 9: 单独提交 current 指针、推送并等待 M2 用户确认**

`CURRENT_RELEASE`、总 manifest 和 CI 切换使用第二个提交：`docs(knowledge): activate flow knowledge 2026-09-12.1`。
M2 未经用户确认，不把任何产品文档从 `pre-static` 切到该 release。

---

### Task 9: M3.1 统一产品定义

**Files:**
- Create: `docs/20_product/PRODUCT_VISION.md`
- Create: `docs/20_product/PRODUCT_SCOPE.md`
- Create: `docs/20_product/USER_AND_WORKSPACES.md`
- Create: `docs/20_product/CAPABILITY_MAP.md`
- Create: `docs/20_product/PRODUCT_BOUNDARIES.md`
- Create: `docs/20_product/RELEASE_SCOPE.md`
- Modify: `docs/README.md`
- Modify: `README.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/00_start_here/DOCUMENT_MAP.md`

- [ ] **Step 1: 建立产品冲突矩阵**

逐项对比 D049、D045/D046、现有 V1 设计、当前实现和知识映射；区分 current、future、historical、rejected。发现真正语义冲突时停止，新增决策，不由迁移者裁决。

- [ ] **Step 2: 写六份单一职责产品文档**

明确公开财报客观分析与授权内部经营分析两阶段；明确不建设总账、不自动因果、不伪造预算/量价/内部事实；能力图严格区分 implemented、designed、external-dependency、out-of-scope。

- [ ] **Step 3: 引用静态知识发布**

六份文档都声明 `knowledge_release: flow-knowledge-2026-09-12.1`，引用产品映射而非 Obsidian 路径或外部文章。

- [ ] **Step 4: 精简根 README**

README 只保留产品简介、运行入口和规范导航；删除过时的瞬时“下一步”正文，改链唯一 current state/roadmap，不复制产品合同。

- [ ] **Step 5: 验证单一产品范围**

Expected: 全仓只有一套 canonical 产品范围；历史设计仍可访问但标明接替关系；产品定义不声称未实现能力。

- [ ] **Step 6: 提交并推送**

Commit: `docs(product): consolidate canonical FLOW product definition`。

### Task 10: M3.2 统一架构与规格，不移动机器合同

**Files:**
- Create: `docs/30_architecture/SYSTEM_ARCHITECTURE.md`
- Create: `docs/30_architecture/DATA_ARCHITECTURE.md`
- Create: `docs/30_architecture/DOMAIN_ARCHITECTURE.md`
- Create: `docs/30_architecture/METRIC_AND_ANALYSIS_ARCHITECTURE.md`
- Create: `docs/30_architecture/SECURITY_AND_DEPLOYMENT.md`
- Create: `docs/40_specs/SPEC_INDEX.md`
- Create: `docs/40_specs/{platform,data-intake,financial-facts,metrics,analysis,operations,reporting,copilot,security}/README.md`
- Modify: `docs/architecture/flow-v1-runtime.md`
- Modify: `docs/architecture/flow-v1-domain-objects.md`
- Modify: `docs/intake/flow-v1-intake.md`
- Modify: `docs/data-contract/flow-v1.md`
- Modify: `docs/metrics/flow-v1-metrics.md`
- Modify: `docs/operations/authentication.md`
- Modify: `docs/superpowers/specs/2026-08-29-flow-v1-design.md`
- Modify: `docs/superpowers/specs/2026-09-01-flow-v1-phase-5-analysis-design.md`
- Modify: `docs/superpowers/specs/2026-09-01-flow-v1-phase-6-dashboard-design.md`
- Modify: `docs/superpowers/specs/2026-09-04-review-repairs-design.md`
- Modify: `docs/superpowers/specs/2026-09-05-flow-metric-dictionary-design.md`
- Modify: `docs/superpowers/specs/2026-09-06-objective-financial-analysis-direction.md`
- Modify: `docs/superpowers/specs/2026-09-09-operations-track-methodology.md`
- Modify: `docs/superpowers/specs/financial-facts-contract.md`

- [ ] **Step 1: 从消费者登记生成 keep/move 清单**

`financial-facts-contract.md` 及被代码/测试引用的机器路径保持原位，在 `SPEC_INDEX.md` 登记为 canonical compatibility path。禁止为了目录整齐复制第二份正文。

- [ ] **Step 2: 编写架构聚合文档**

每份明确 current/designed/external-dependency/out-of-scope；使用链接组合现有细节，不重复机器合同和实现数据。

- [ ] **Step 3: 为每个规格分域建立索引**

索引必须记录 spec ID、状态、知识 release、决策、代码、验收和物理路径。现有规格若保持原位，索引指向原路径。

- [ ] **Step 4: 更新可变规格元数据**

只补身份、状态、release 和接替关系；遇到公式、输入输出、不变量、权限或失败态的语义变化，停止并走正式决策/规格评审，不能当作“文档更新”。

- [ ] **Step 5: 验证机器消费者**

至少运行：

```bash
cd services/api
uv run pytest tests/data_contract/test_committed_artifacts.py \
  tests/statements/test_fact_contract.py \
  tests/metrics/test_dictionary_execution_parity.py -q
```

Expected: PASS；所有已登记硬编码路径继续存在。

- [ ] **Step 6: 提交、推送并等待 M3 验收**

Commit: `docs(specs): consolidate architecture and specification authority`。

---

### Task 11: M4 建立唯一当前路线图和稳定工作包

**Files:**
- Create: `docs/50_plans/CURRENT_ROADMAP.md`
- Create: `docs/50_plans/work_items/README.md`
- Create: `docs/50_plans/work_items/U04--independent-oracle.md`
- Create: `docs/50_plans/work_items/U08--production-readiness.md`
- Create: `docs/50_plans/work_items/U09-O05--authorized-internal-pilot.md`
- Create: `docs/50_plans/work_items/U10--v1-1-evidence-decision.md`
- Create: `docs/50_plans/views/active.md`
- Create: `docs/50_plans/views/blocked.md`
- Create: `docs/50_plans/views/completed.md`
- Modify: `docs/superpowers/plans/2026-09-07-unified-next-plan.md`
- Modify: `docs/superpowers/plans/2026-09-09-operations-track-plan.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/README.md`
- Modify: `README.md`

- [ ] **Step 1: 在执行时重新核对实际状态**

不得使用本计划编写时的 U8/U4/U9/U10 状态直接生成路线图。只依据届时已推送提交、CI、外部到料和用户授权重新确定 active/blocked/completed。

- [ ] **Step 2: 写唯一路线图**

路线图只含顺序、依赖、状态、工作包链接和最近证据；不复制规格、知识或详细步骤。

- [ ] **Step 3: 创建稳定工作包**

每个工作包引用 approved spec、accepted decision、产品映射、knowledge release、验收和授权边界。已完成 U/O 项只进入 generated completed view，不重新创建可领取任务。

- [ ] **Step 4: 把旧计划标为历史接替**

旧统一计划和经营计划保留原始任务细节，顶部新增 `superseded_by: FLOW-PLAN-CURRENT`、`do_not_execute: true`；不改写历史 checkbox 和提交证据。

- [ ] **Step 5: 生成视图**

active/blocked/completed 由元数据生成，禁止移动工作包表达状态。

- [ ] **Step 6: 验证唯一执行入口**

Expected: 恰有一个 `CURRENT_ROADMAP.md`；旧 Phase/WS/M/P/U/O 历史文档不再自称当前总计划；所有 active 工作包通过 approved-spec 门禁。

- [ ] **Step 7: 提交、推送并等待 M4 验收**

Commit: `docs(planning): establish canonical roadmap and work items`。

---

### Task 12: M5.1 整理可变历史文档并保留兼容入口

**Files:**
- Create: `docs/90_archive/plan-index.md`
- Create: `docs/90_archive/spec-index.md`
- Create: `docs/90_archive/review-index.md`
- Create: `docs/90_archive/path-compatibility.tsv`
- Modify: `docs/documentation-status.md`
- Modify: `docs/00_start_here/DOCUMENT_MAP.md`
- Modify: `HANDOFF.md`（迁至 `docs/knowledge-base/07_handoff/`，设计 V1.1 §5.2）
- Modify: `Finance_Intelligence_OS_完整会话归档.md`（迁至 `docs/90_archive/`）
- Modify: files marked `move` or `archive` in `path-map.tsv`
- Modify: all mutable consumers listed for those paths
- Create: compatibility entries at old paths where consumers cannot move

- [ ] **Step 1: 冻结本批移动清单**

从 `path-map.tsv` 选择一个最多 20 文件的小批次；记录源哈希、目标、消费者和回滚提交。raw/original/原图/approved 以及机器 keep 路径不得进入。

- [ ] **Step 2: 先更新可变消费者**

修改 README、索引和可变说明中的链接；不可变档案中的旧链接不改，必须由兼容入口或 `DOCUMENT_MAP.md` 解释。

- [ ] **Step 3: 使用 `git mv` 移动已批准文件**

一次只移动当前小批次。历史文件增加 archived 元数据、接替 ID 和 `do_not_execute: true`，不改写历史事实。

- [ ] **Step 4: 为未清零消费者保留兼容入口**

兼容入口只导航，不复制正文；`path-compatibility.tsv` 记录消费者、建立 release、最早移除 release 和审批状态。

- [ ] **Step 5: 执行链接、消费者和不可变校验**

任一失败用新的 forward revert 提交撤回本小批次，不使用 `reset --hard` 或强推。

- [ ] **Step 6: 小批次提交并推送**

Commit: `docs(archive): migrate legacy documentation batch <n>`。
重复 Step 1–6，直到所有 M0 可变文档均有最终处置。

### Task 13: M5.2 退役手工状态登记，建立生成索引

**Files:**
- Create: `docs/60_delivery/generated/DOCUMENT_STATUS.md`
- Create: `docs/60_delivery/generated/document-inventory.tsv`
- Modify: `scripts/documentation/inventory.py`
- Modify: `docs/documentation-status.md`
- Modify: `docs/README.md`
- Modify: `docs/00_start_here/DOCUMENT_MAP.md`

- [ ] **Step 1: 写生成一致性测试**

测试 `DOCUMENT_STATUS.md` 完全由文档元数据、Git 和 path map 生成；手改后 `--check` 必须失败。

- [ ] **Step 2: 生成全量状态视图**

列出当前、历史、legacy-exempt、机器路径和知识资产，但不重复正文中的状态解释。

- [ ] **Step 3: 将旧 `documentation-status.md` 改为兼容入口**

保留历史核对记录的 Git 可追溯性，当前内容只链接生成视图和 `DOCUMENT_MAP.md`。

- [ ] **Step 4: 验证并提交**

Commit: `docs(status): replace manual registry with generated inventory`。
M5 验收必须证明无移动中的路径、无未登记兼容入口、不可变基线完全一致。

---

### Task 14: M6.1 建立全仓链接、发布和消费者总门禁

**Files:**
- Create: `scripts/documentation/links.py`
- Create: `scripts/tests/test_document_links.py`
- Create: `docs/10_governance/link-allowlist.tsv`
- Create: `docs/60_delivery/verification/2026-09-12--verification--documentation-migration--v1.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `Makefile`

- [ ] **Step 1: 写断链和逃逸失败测试**

覆盖相对链接、目录链接、锚点、中文/空格路径、不可变档案 allowlist、仓库外逃逸和兼容入口循环。HTTP 链接只登记，不把瞬时网络可达性作为 CI 硬门禁。

- [ ] **Step 2: 实现链接检查器**

默认扫描除 raw/original 字节档案外的 Markdown；历史故意断链必须在 allowlist 中记录来源、旧目标、接替入口和原因。

- [ ] **Step 3: 增加 `make docs-check`**

命令顺序：元数据→链接→inventory 漂移→immutable lock→knowledge release→reader rubric schema。任何一步失败返回非零。

- [ ] **Step 4: 接入 static-python CI**

继续使用现有 16 job，不新增 job；添加 `make docs-check`。更新 `test_ci_gate_inventory.py` 只在命令合同确有变化时调整，不能放宽已有门禁。

- [ ] **Step 5: 运行本地总门禁**

Run: `make docs-check && cd services/api && uv run python -m unittest discover -s ../../scripts/tests -v`
Expected: PASS；零未登记断链、零哈希漂移、零权威入口重复。

- [ ] **Step 6: 记录验证证据**

验证文档记录提交、命令、计数、allowlist、兼容入口、发布 ID、不可变 hash 和已知非阻塞边界；不得声称应用功能因文档门禁而重新验收。

- [ ] **Step 7: 提交并推送**

Commit: `ci(docs): enforce documentation and knowledge integrity`。

### Task 15: M6.2 执行固定五题无上下文接续测试

**Files:**
- Create: `docs/80_reviews/reader-test/QUESTIONS--v1.0.md`
- Create: `docs/80_reviews/reader-test/RUBRIC--v1.0.yaml`
- Create: `docs/80_reviews/reader-test/EXPECTED-ANSWERS--v1.0.md`
- Create: `docs/80_reviews/reader-test/RUN-<date>-<agent-id>.md`
- Create: `scripts/documentation/reader_rubric.py`
- Create: `scripts/tests/test_reader_rubric.py`
- Modify: `docs/knowledge-base/99_manifest/READER_TEST.md`
- Modify: `docs/60_delivery/verification/2026-09-12--verification--documentation-migration--v1.md`

- [ ] **Step 1: 固定题目和 rubric 后再邀请读者**

使用设计规范 V1.1 `10.3` 的五题。每题列必答事实、规范来源、允许表述、关键错误和分值；第 1、2、4 题标记 critical。

- [ ] **Step 2: 校验 rubric 可评分**

Run: `cd services/api && uv run python ../../scripts/documentation/reader_rubric.py validate docs/80_reviews/reader-test/RUBRIC--v1.0.yaml`
Expected: 5 题、critical 集合准确、总分和通过规则有效。

- [ ] **Step 3: 派发一个无历史上下文的独立 Agent**

只给 `READING_ORDER.md` 指定的最多五份起点文档和五题，不给本迁移会话、期望答案或 rubric。

- [ ] **Step 4: 原样保存回答并盲评**

保存实际回答、逐题证据和评分。通过要求：至少 4/5 完全满足，且三道 critical 题无关键错误。

- [ ] **Step 5: 失败时只修权威文档或导航**

不得为了让测试通过放宽 rubric。修改后增加 rubric/expected answer 版本或新 run，不覆盖旧失败证据。

- [ ] **Step 6: 更新历史 reader test 入口**

`knowledge-base/99_manifest/READER_TEST.md` 只链接新测试体系，并明确旧记录是历史快照。

- [ ] **Step 7: 提交并推送**

Commit: `test(docs): verify context-free project handoff`。

### Task 16: M6.3 最终迁移验收与关闭

**Files:**
- Create: `docs/60_delivery/releases/2026-09-12--release--documentation-system-v1.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/README.md`
- Modify: `docs/knowledge-base/README.md`
- Modify: `docs/60_delivery/verification/2026-09-12--verification--documentation-migration--v1.md`
- Modify: `docs/knowledge-base/99_manifest/inventory.tsv`
- Modify: `docs/knowledge-base/99_manifest/sha256sums.txt`

- [ ] **Step 1: 重跑 M0–M6 全部门禁**

```bash
make docs-check
cd services/api && uv run python -m unittest discover -s ../../scripts/tests -v
git diff --check
```

Expected: 全部 PASS；immutable baseline 与所有 delta 可重放；current release 可恢复；唯一入口断言通过。

- [ ] **Step 2: 验证 Obsidian 脱离**

在不允许访问 `/Users/qiming/ObsidianWiki/` 的测试环境中，仅用仓库文档回答固定五题并定位来源、知识、产品、规格、计划和交付证据。

- [ ] **Step 3: 核对 Git 范围**

确认没有产品代码语义变更、没有原始档案字节变更、没有其他任务文件；若迁移过程中必须改程序消费者路径，该项须有单独规格和测试证据，不能隐藏在最终提交。

- [ ] **Step 4: 写发布记录**

记录 M0–M6 的提交、用户批准、知识 release、兼容入口、永久 keep 路径、allowlist、reader test 和尚未移除的历史入口。

- [ ] **Step 5: 更新当前状态**

`PROJECT_STATE.md` 只记录“静态知识和文档体系已迁移”的事实与剩余边界；不得把历史迁移步骤留作当前待办。

- [ ] **Step 6: 重建知识库 manifest**

验证清单不含自身、排序稳定、旧不可变哈希未变。

- [ ] **Step 7: 提交、推送并等待 GitHub CI**

Commit: `docs(release): complete static knowledge and documentation migration`。
只有远端推送成功、CI 通过、M6 读者测试通过并取得用户确认，迁移才可标记 complete。

## 3. 批次验收摘要

| 批次 | 通过条件 | 主要回滚触发 |
|---|---|---|
| M0 | 全量清单、消费者、路径图和不可变锁可重复 | 漏掉机器消费者或不可变根 |
| M1 | 唯一 current state、schema/CI、D001–D051 完整 | 当前入口重复、决策语义被改 |
| M2 | 来源覆盖与 M0 基线闭合、知识资产复核、release lock 可恢复 | 伪造来源、敏感泄露、哈希不符 |
| M3 | 一套产品范围、规格索引完整、机器路径通过 | 把目标当现状、改变合同 |
| M4 | 唯一路线图、工作包稳定、旧计划不可执行 | 第二总计划、状态引用旧证据 |
| M5 | 所有可变文档有处置、兼容入口登记 | 断链、历史事实被重写 |
| M6 | `docs-check`、CI、五题接续测试和 Obsidian 脱离通过 | critical 误读、不可恢复发布 |

## 4. 明确延后事项

- 兼容入口不会在首轮迁移中删除；最早在消费者清单归零并连续两个含消费者验证的正式发布周期通过后，另行批准删除。
- 本计划不刷新 2026-09-12 15:46 之后的 Obsidian 内容；未来增量使用新的 snapshot 和知识 release。
- 本计划不重构 P5 生成数据路径、不迁移原始财报样本、不修改财务公式、不建设新产品功能。
- 任何发现的产品、会计或权限问题形成独立 decision/spec/work item，不夹带进文档迁移提交。

## 5. 执行完成定义

迁移只有同时满足以下条件才完成：

1. M0–M6 每批均有明确批准、验证、提交和推送记录；
2. FLOW 日常设计、计划和实施不再依赖动态 Obsidian；
3. 基线全量来源覆盖可追溯，canonical 知识通过版本化 release lock 恢复；
4. 全仓只有一个当前状态、一条当前路线图和一套 canonical 产品范围；
5. 不可变档案基线逐文件哈希未变；
6. 所有机器消费者路径通过，兼容入口均已登记；
7. 无上下文 Agent 在最多五份起点文档内通过固定五题；
8. GitHub CI 通过，最终用户确认迁移关闭。
