---
doc_id: FLOW-PLAN-KNOWLEDGE-REFRESH-002
title: FLOW 第二代静态知识刷新与战略重基线实施计划
doc_type: plan
status: archived
version: 1.2
created_at: 2026-09-18
updated_at: 2026-09-24
owner: FLOW
decision_refs: [D051, D052, D053, D054]
knowledge_release: flow-knowledge-2026-09-12.1
depends_on: [FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
acceptance_refs: [FLOW-DESIGN-KNOWLEDGE-REFRESH-002]
supersedes: []
superseded_by: FLOW-PLAN-INTEGRATED-EXECUTION-20260924
do_not_execute: true
---

# FLOW 第二代静态知识刷新与战略重基线 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for code changes and `superpowers:verification-before-completion` before every completion claim.

**Goal:** 在不恢复 FLOW 对动态 Obsidian 依赖的前提下，先验收 Davybase 已有图片批次，再补齐核心非微信图片覆盖，冻结批次结束后的首个稳定 15:00 Git 截面，重建可追溯静态知识 release，并在用户正式裁决后原子更新产品目标与路线图。

**Architecture:** Davybase 负责 L1 机器语义和统一运行清单；ObsidianWiki 只作为受锁定的上游来源仓库；FLOW 负责 L0 来源基线、L2 审查综合、sealed candidate、L3 决策采用和原子激活。三个仓库分别提交，任何阶段都不得把未审查的模型输出直接提升为产品事实。

**Tech Stack:** Python 3、pytest/unittest、Git tree/commit、Markdown/YAML/TSV/JSONL、现有 FLOW 文档门禁和知识 release 工具。

**Spec:** `docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md`

## Global Constraints

- 旧基线固定为 Obsidian tree `36274b2463aad9eae069af805e53e937c704c381`、机器分母 3,317；不得用 birth time、mtime 或运行中计数替代。
- 原始档案、旧 release 和 `2026-09-17-obsidian-delta-scan.md` 不覆盖；订正以新增文件完成。
- 敏感/排除目录 fail closed：只允许聚合数量，不允许路径、标题、作者、逐文件哈希或正文进入 FLOW 或外部模型。
- Davybase 图片/文本生成统一使用内容 SHA-256、run manifest schema、完整代码 commit、输入 tree、提示 SHA-256、模型参数和输出 SHA-256。
- `CURRENT_RELEASE` 在 sealed candidate、独立复验、战略影响评估和用户裁决完成前保持不变。
- S1 是人工决策门：执行者只能提交提案，不得替用户接受、修订或拒绝战略变更。
- 三仓库每个原子任务只提交本任务文件；禁止强推和覆盖历史。
- K2 accepted manifest 是日期和发布身份的唯一权威输入。下文 `<SNAPSHOT_DATE>`、`<SNAPSHOT_ID>`、`<RELEASE_ID>` 只能在 K2 成功后解析；不得从计划文件日期推导。`<RELEASE_ID>` 必须是 `flow-knowledge-<SNAPSHOT_DATE>.N`。

## Mandatory Micro-Protocol

每个代码任务必须逐项执行并把命令、返回码和关键输出写进任务证据：

- [ ] 先添加一个最小失败测试，并用精确 selector 运行；预期 `FAIL`，且失败原因必须是待实现合同。
- [ ] 只实现让该测试通过的最小代码；同一 selector 预期 `PASS`。
- [ ] 运行该模块完整测试，再运行仓库相关门禁；预期全部 `PASS`。
- [ ] 执行 `git diff --check`、范围检查和敏感路径扫描。
- [ ] 只提交任务文件，记录完整 commit SHA，并推送规范 remote；推送失败不得声称任务完成。

Python 测试命令以仓库实际环境为准：FLOW 使用 `python3 -m unittest <module-or-selector>`；Davybase 使用 `.venv/bin/python -m pytest <path>::<test> -q`。如果实际测试框架不同，先在证据中记录发现和等价命令，不得跳过红绿循环。

FLOW 固定门禁命令（除非任务明确在红灯阶段）均须返回 0；`check_docs.py`、manifest、links 和单元测试应出现各自既有 PASS/OK 摘要，`metadata.py --check` 当前成功时允许静默：

```bash
python3 scripts/check_docs.py --phase m6
python3 scripts/documentation/metadata.py --check
python3 scripts/documentation/links.py --check
python3 scripts/documentation/kb_manifest.py --check
python3 -m unittest scripts.tests.test_decision_integrity
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
git diff --check
```

---

### Task 0: 批准规格、固定执行身份与前置证据

**Files:**
- Modify: `docs/superpowers/specs/2026-09-17-static-knowledge-refresh-and-strategic-rebaseline-design.md`
- Modify: `docs/40_specs/SPEC_INDEX.md`
- Create: `docs/knowledge-base/02_research/synthesis/2026-09-18-refresh-preflight.md`
- Test: `scripts/tests/test_document_metadata.py`

**Steps:**

1. [ ] 将规格状态从 `review` 改为 `approved`，更新时间改为 `2026-09-18`；正文不得改写已审查合同，并在 `SPEC_INDEX` 登记同一路径和 approved 状态。
2. [ ] 记录 FLOW、Davybase、ObsidianWiki 的 canonical remote、完整 HEAD/tree、clean/dirty、当前 release、Davybase 图片批次最终统计 `1241/1265 + 24 decoration-only`，并标出哪些是上游事实、哪些待复验。
3. [ ] 运行 `python3 scripts/documentation/metadata.py --check`、`python3 scripts/documentation/require_approved_specs.py FLOW-DESIGN-KNOWLEDGE-REFRESH-002` 和 `git diff --check`，预期全部 PASS。
4. [ ] 提交并推送 FLOW 前置证据：`docs: approve knowledge refresh execution baseline`。

**Acceptance:** 三仓库身份可重放，规格为 approved，当前 release 未变化。

### Task 1: Davybase 统一审计 envelope 与内容哈希（K0）

**Repositories:** `/Users/qiming/workspace/davybase` + `/Users/qiming/ObsidianWiki`

**Files:**
- Modify: `scripts/run/image_digest.py`
- Modify: `scripts/run/note_summary.py`
- Create: `scripts/run/knowledge_run_manifest.py`
- Create: `tests/test_knowledge_run_manifest.py`
- Modify/Create: image digest and note summary unit tests under `tests/`

**Steps:**

1. [ ] 在 `tests/test_knowledge_run_manifest.py` 添加同名同大小异内容、附录剥离、缺必需 envelope、互斥终态测试；运行 `.venv/bin/python -m pytest tests/test_knowledge_run_manifest.py -q`，预期因模块不存在或合同未实现而 FAIL。
2. [ ] 实现规范化 LF/NFC、正文/单图/图片集合 SHA-256 和机器附录剥离；重跑目标测试预期 PASS。
3. [ ] 定义 `davybase-knowledge-run/v1` JSONL schema，记录 run/document/image/result 四类记录及互斥终态。
4. [ ] 将两条脚本接入 envelope，保留旧 frontmatter 读取兼容；添加 dry-run 零写入、异常记录、汇总对账测试。
5. [ ] 运行 `.venv/bin/python -m pytest tests/test_knowledge_run_manifest.py tests/test_image_digest.py tests/test_note_summary.py -q` 和 `.venv/bin/python -m pytest tests -q`；均须返回 0，摘要行不得含 failed/error。
6. [ ] 提交并推送：`feat: make knowledge enrichment runs auditable`。

**Acceptance:** 内容变化可检测；1241 批次可以补建 retrospective manifest；新运行可按 run ID 完整审计。

### Task 2: 验收既有 Davybase 图片批次并封存 K0 证据

**Repositories:** Davybase + FLOW

**Files:**
- Create in Davybase: `docs/evidence/2026-09-18-image-batch-acceptance.md`
- Create in Davybase: `docs/evidence/runs/<K0_RUN_ID>.jsonl`
- Create in FLOW: `docs/knowledge-base/02_research/synthesis/2026-09-18-davybase-image-batch-acceptance.md`

**Steps:**

1. [ ] 在任何 K1 apply 之前记录 Obsidian 的 pre-K1 完整 commit/tree、Davybase 原批次 commit、输入 universe 和输出 universe。
2. [ ] 从文档 frontmatter 和图片附录重算 1,265 个输入终态；验证 1,241 成功、24 decoration-only，或记录实测订正。
3. [ ] 抽样验证至少 30 篇：内容哈希、图片顺序、原图可定位、摘要与图片段存在、失败数真实。
4. [ ] 对旧批次构造 `retrospective=true` manifest。不可恢复必需字段必须标记 `nonconformant`：缺 code commit/input tree/prompt hash 的条目不得计入完整 L1 coverage、不得支撑 HIGH/L2；只有重跑或用户批准的正式例外合同才能解除。
5. [ ] FLOW 只复制汇总、定位符和哈希，不复制全部原文/图片。
6. [ ] 两仓库分别运行文档/测试门禁、提交并推送；提交后才允许 Task 3 写 Obsidian。

精确验收命令合同（返回 0，输出 `retrospective manifest: PASS (inputs=1265, success=1241, filtered=24)`；实测不符时返回非零并先订正报告，不能改 expected 掩盖差异）：

```bash
cd /Users/qiming/workspace/davybase
.venv/bin/python scripts/run/knowledge_run_manifest.py retrospective \
  --vault /Users/qiming/ObsidianWiki \
  --scope processed/微信知识库 \
  --pre-k1-commit <PRE_K1_COMMIT> --pre-k1-tree <PRE_K1_TREE> \
  --batch-code-commit <ORIGINAL_BATCH_COMMIT> \
  --expected-inputs 1265 --expected-success 1241 --expected-filtered 24 \
  --output docs/evidence/runs/<K0_RUN_ID>.jsonl
.venv/bin/python scripts/run/knowledge_run_manifest.py verify \
  --manifest docs/evidence/runs/<K0_RUN_ID>.jsonl --strict
```

**Acceptance:** “完成”由机器对账与抽样支撑；pre-K1 tree、旧批次 universe 与 nonconformance 均已冻结并推送。

### Task 3: 泛化非微信图片覆盖并建立安全边界（K1）

**Repository:** `/Users/qiming/workspace/davybase`

**Files:**
- Modify: `scripts/run/image_digest.py`
- Create: `config/knowledge_enrichment_scope.yaml`
- Create: `scripts/run/image_coverage.py`
- Create/Modify: corresponding tests under `tests/`
- Generated (gitignored if operational): `.davybase/progress/<run-id>/coverage.json`
- Generated: `.davybase/progress/<run-id>/obsidian-pathspec.txt`

**Steps:**

1. [ ] 添加 selector `tests/test_image_digest.py::test_scope_rejects_sensitive_and_escape`，覆盖允许目录以及绝对路径、`..`、符号链接逃逸、`个人信息备份`、`15_户外、徒步`；先运行并确认因 scope 合同未实现而 FAIL。
2. [ ] 将 `--account` 泛化为 allowlist `--scope/--dir`，保留原命令兼容；图片解析采用 vault 最短路径语义并报告 missing/ambiguous/unsupported/decorative；重跑 selector 预期 PASS。
3. [ ] 添加并运行 coverage 测试，随后实现只读扫描：每个业务目录输出 Markdown、含图文档、图片引用、可解析、已解释、待解释、过滤和失败数。
4. [ ] 对非微信核心目录执行 dry-run，保存命令/coverage；人工抽查至少 20 个路径解析结果，确认敏感或无关输入为零。
5. [ ] 以独立 run ID 执行 apply，失败项有界重试；不得把失败视为完成。
6. [ ] 生成 K1 最终 manifest、例外清单和 coverage；运行 `.venv/bin/python -m pytest tests/test_image_digest.py tests/test_knowledge_run_manifest.py -q` 与 `.venv/bin/python -m pytest tests -q`，均须返回 0。
7. [ ] 用 `image_coverage.py scope-check` 生成 UTF-8/LF、每行一个 vault 相对路径的 `obsidian-pathspec.txt`；拒绝空行、tab/newline 文件名、范围外路径和非 K1 机器附录差异。只用该 pathspec 暂存 Obsidian 变化，提交并推送 canonical remote；记录完整 commit/tree，确认 `git status --porcelain=v1 --untracked-files=all` 输出为空。
8. [ ] 提交并推送 Davybase：`feat: extend image knowledge coverage to core domains`。两个仓库都成功推送后 Task 3 才完成。

精确运行合同（每个成功命令返回 0，并输出末尾所示 PASS；失败重试后仍失败的条目留在 exception，不得伪装成功）：

```bash
cd /Users/qiming/workspace/davybase
.venv/bin/python scripts/run/image_coverage.py scan \
  --vault /Users/qiming/ObsidianWiki \
  --scope processed/02_企业管理 --scope processed/03_财务与会计 --scope processed/04_跨境物流 \
  --output .davybase/progress/<K1_RUN_ID>/coverage-before.json
.venv/bin/python scripts/run/image_digest.py \
  --vault /Users/qiming/ObsidianWiki \
  --dir processed/02_企业管理 --dir processed/03_财务与会计 --dir processed/04_跨境物流 \
  --dry-run --run-id <K1_RUN_ID> --manifest .davybase/progress/<K1_RUN_ID>/run.jsonl
.venv/bin/python scripts/run/image_digest.py \
  --vault /Users/qiming/ObsidianWiki \
  --dir processed/02_企业管理 --dir processed/03_财务与会计 --dir processed/04_跨境物流 \
  --apply --run-id <K1_RUN_ID> --manifest .davybase/progress/<K1_RUN_ID>/run.jsonl
.venv/bin/python scripts/run/image_digest.py \
  --vault /Users/qiming/ObsidianWiki --retry-from .davybase/progress/<K1_RUN_ID>/run.jsonl \
  --apply --run-id <K1_RETRY_RUN_ID> --manifest .davybase/progress/<K1_RETRY_RUN_ID>/run.jsonl
.venv/bin/python scripts/run/image_coverage.py scope-check \
  --vault /Users/qiming/ObsidianWiki --run-manifest .davybase/progress/<K1_RUN_ID>/run.jsonl \
  --pathspec .davybase/progress/<K1_RUN_ID>/obsidian-pathspec.txt
cd /Users/qiming/ObsidianWiki
git add --pathspec-from-file=/Users/qiming/workspace/davybase/.davybase/progress/<K1_RUN_ID>/obsidian-pathspec.txt
git diff --cached --check
git commit -m 'docs: add audited core-domain image knowledge'
git push origin main
git status --porcelain=v1 --untracked-files=all
```

scan/dry-run/apply/retry/scope-check 分别输出 `coverage scan: PASS`、`image digest dry-run: PASS`、`image digest apply: PASS`、`image digest retry: PASS`、`scope check: PASS`；最后 status 输出为空。

**Acceptance:** 核心非微信含图文档全部进入 success/filtered/failed/review 之一；状态总数等于输入总数；敏感输入为零。

### Task 4: 执行稳定 15:00 Obsidian Git 截面（K2）

**Repository:** `/Users/qiming/ObsidianWiki`

**Files:**
- Create in Davybase: `scripts/run/freeze_snapshot.py`
- Create in Davybase: `tests/test_freeze_snapshot.py`
- Create in Davybase: `docs/evidence/snapshots/<SNAPSHOT_ID>.json`

**Steps:**

1. [ ] 先写 `tests/test_freeze_snapshot.py`：缺锁、tree 漂移、dirty、远端不可获取必须 FAIL；accepted manifest 必须含 lock owner/token、14:30/15:00/15:30、writer 枚举、两次 HEAD/tree/status、文件数、字节数、remote 和原因。
2. [ ] 实现冻结器并让测试 PASS；任何日期只从实际候选时间生成。
3. [ ] 在首个可用日 14:30 Asia/Shanghai 获取排他锁；检查 Davybase、同步、备份和人工 writer 已停止，工作树包含 untracked 在内为空。
4. [ ] 15:00 记录候选；15:30 再次验证锁、HEAD/tree、clean 和 writer。任一失败写 committed `rejected` manifest 并顺延下一稳定 15:00。
5. [ ] 对 accepted commit/tree 执行 canonical remote object fetch 或 clean clone 验证；不可从远端获得则拒绝。
6. [ ] 将 `docs/evidence/snapshots/<SNAPSHOT_ID>.json` 提交并推送 Davybase，记录其 SHA-256 后释放锁。不得为制造 clean 自动提交未知用户修改。

冻结命令合同（`<FREEZE_MANIFEST>` 为 `docs/evidence/snapshots/<SNAPSHOT_ID>.json`；成功分别输出 `freeze lock: ACQUIRED`、`freeze candidate: RECORDED`、`freeze verify: ACCEPTED`、`freeze lock: RELEASED`，任何 rejected 返回非零）：

```bash
cd /Users/qiming/workspace/davybase
.venv/bin/python scripts/run/freeze_snapshot.py acquire \
  --vault /Users/qiming/ObsidianWiki --timezone Asia/Shanghai \
  --lock-id <FREEZE_LOCK_ID> --manifest <FREEZE_MANIFEST>
.venv/bin/python scripts/run/freeze_snapshot.py candidate \
  --vault /Users/qiming/ObsidianWiki --at 15:00 --manifest <FREEZE_MANIFEST>
.venv/bin/python scripts/run/freeze_snapshot.py verify \
  --vault /Users/qiming/ObsidianWiki --at 15:30 --canonical-remote origin \
  --manifest <FREEZE_MANIFEST>
git add <FREEZE_MANIFEST>
git commit -m 'docs: freeze <SNAPSHOT_ID> evidence'
git push origin main
.venv/bin/python scripts/run/freeze_snapshot.py release \
  --lock-id <FREEZE_LOCK_ID> --manifest <FREEZE_MANIFEST>
```

脚本必须校验本机实际时钟位于指定分钟窗口（容差不超过 60 秒），不得仅相信 `--at` 文本。若 candidate/verify 失败，先将 rejected manifest 提交推送，再 release lock。

**Acceptance:** candidate 与 verification 的 commit/tree 完全相同且仓库 clean；有明确 accepted/rejected 终态。

### Task 5: 重建 FLOW 来源基线和四维差异（K3）

**Repository:** FLOW

**Files:**
- Modify: `scripts/documentation/source_baseline.py`
- Modify: `scripts/tests/test_source_baseline.py`
- Create: `docs/knowledge-base/00_governance/migration/source-inputs-<SNAPSHOT_DATE>.yaml`
- Create: `docs/knowledge-base/00_governance/migration/source-id-registry-<SNAPSHOT_DATE>.tsv`
- Create: `docs/knowledge-base/10_sources/snapshots/<SNAPSHOT_ID>.yaml`
- Create: `docs/knowledge-base/10_sources/source-baseline-<SNAPSHOT_DATE>.tsv`
- Create: `docs/knowledge-base/10_sources/source-diff-<SNAPSHOT_DATE>.tsv`

**Steps:**

1. [ ] 在 `scripts/tests/test_source_baseline.py` 添加 NFC/LF、附录剥离、registry 跨改名、四维共存、唯一终态和 snapshot-date/release-date mismatch 测试；运行该模块，预期新测试 FAIL。
2. [ ] 扩展构建器以 Git blob/tree 和 Task 4 accepted manifest 为唯一输入；禁用 mtime/birthtime；运行该模块预期 PASS。
3. [ ] 对 sensitive/excluded 只输出不可逆聚合；添加泄漏 fixture 并确认构建 fail closed。
4. [ ] 从旧 tree 到新 tree 生成 baseline/diff 并对账；运行 `python3 -m unittest scripts.tests.test_source_baseline`。
5. [ ] 重跑两次并比较 SHA-256；提交并推送本任务资产。

正式构建命令合同（Task 5 实现该 CLI 后使用；返回 0，最后一行须为 `source baseline v2: PASS`）：

```bash
python3 scripts/documentation/source_baseline.py build-v2 \
  --snapshot-manifest <K2_ACCEPTED_MANIFEST> \
  --previous-tree 36274b2463aad9eae069af805e53e937c704c381 \
  --input-manifest docs/knowledge-base/00_governance/migration/source-inputs-<SNAPSHOT_DATE>.yaml \
  --registry docs/knowledge-base/00_governance/migration/source-id-registry-<SNAPSHOT_DATE>.tsv \
  --baseline docs/knowledge-base/10_sources/source-baseline-<SNAPSHOT_DATE>.tsv \
  --diff docs/knowledge-base/10_sources/source-diff-<SNAPSHOT_DATE>.tsv
python3 scripts/documentation/source_baseline.py check-v2 \
  --snapshot-manifest <K2_ACCEPTED_MANIFEST> \
  --baseline docs/knowledge-base/10_sources/source-baseline-<SNAPSHOT_DATE>.tsv \
  --diff docs/knowledge-base/10_sources/source-diff-<SNAPSHOT_DATE>.tsv
```

**Acceptance:** 旧分母 3,317 保持；新分母和各差异维度有等式对账；相同 tree 重跑字节一致。

### Task 6: 全量路由、高价值精读与 L2 知识综合（K4）

**Files:**
- Create: `docs/knowledge-base/02_research/synthesis/<SNAPSHOT_DATE>-obsidian-refresh-final-report.md`
- Create: `docs/knowledge-base/10_sources/coverage-<SNAPSHOT_DATE>.tsv`
- Create: `docs/knowledge-base/10_sources/image-exceptions-<SNAPSHOT_DATE>.tsv`
- Create: `scripts/documentation/coverage_validator.py`
- Create: `scripts/tests/test_coverage_validator.py`
- Create: `docs/knowledge-base/00_governance/change-manifests/<SNAPSHOT_ID>-l2.tsv`
- Create: `docs/knowledge-base/30_domain_handbooks/product_experience/README--v1.0.md`
- Create: `docs/knowledge-base/30_domain_handbooks/knowledge_ai_engineering/README--v1.0.md`
- Modify: `docs/knowledge-base/50_product_mappings/FLOW-PRODUCT-MAPPING--v1.0.md`
- Create: `docs/knowledge-base/50_product_mappings/adoption-register-<SNAPSHOT_DATE>.tsv`

**Steps:**

1. [ ] 先写 coverage validator 红灯测试：universe/分母/分子/排除理由、互斥终态、HIGH >5%、不可读 >1%、敏感外发必须阻断；每个知识域还必须有 `systematic_misclassification_reviewed,systematic_misclassification,reviewer_id,review_reason`，每个来源/格式/主题分组必须有 `failure_concentration_reviewed,failure_concentration,reviewer_id,review_reason`。任一 `reviewed=false`/缺失或任一结论 `true` 都阻断 K5，并为 false→true、缺失→false 两侧写边界测试。
2. [ ] 实现 validator 并运行 `python3 -m unittest scripts.tests.test_coverage_validator` 预期 PASS；在路由开始前冻结 HIGH rubric、override 格式、双审人身份和上述两类人工裁决字段。人工判断必须有理由且不可由同一自动路由器自审。
3. [ ] 对 allowlist 核心来源执行摘要/附录级全量 K1–K10 路由；失败项先人工最小筛查。
4. [ ] HIGH 全量回读；MED/LOW 双分层双审。触发任一停止条件即修正规则并重跑受影响分层。
5. [ ] 在编辑任何 L2 资产前生成并人工审查 `<SNAPSHOT_ID>-l2.tsv`，列固定为 `operation,path,evidence_refs,owner,review_status`；`path` 必须是无通配符的仓库相对路径，`review_status` 必须为 `approved`。后续只能创建/修改清单中的知识卡、手册和方法资产。
6. [ ] 最终报告显式订正历史预扫描；运行下列命令，均须返回 0 且输出 `coverage: PASS`/固定门禁 PASS 后提交推送。

```bash
python3 scripts/documentation/coverage_validator.py \
  --coverage docs/knowledge-base/10_sources/coverage-<SNAPSHOT_DATE>.tsv \
  --exceptions docs/knowledge-base/10_sources/image-exceptions-<SNAPSHOT_DATE>.tsv \
  --change-manifest docs/knowledge-base/00_governance/change-manifests/<SNAPSHOT_ID>-l2.tsv \
  --strict
python3 scripts/check_docs.py --phase m6
```

**Acceptance:** 目录全量、语义全量、高价值精读三层均有分母；HIGH 漏检率 ≤5%；所有输入有终态。

### Task 7: 构建并封存 sealed candidate（K5）

**Files:**
- Modify: `scripts/documentation/knowledge_release.py`
- Modify: `scripts/tests/test_knowledge_release.py`
- Modify: `scripts/documentation/reader_rubric.py`
- Create/Modify: `scripts/tests/test_reader_rubric.py`
- Create: `docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/{questions.yaml,expected.yaml,rubric.yaml,results.yaml}`
- Create: `docs/knowledge-base/00_governance/releases/<RELEASE_ID>/{release.yaml,coverage.tsv,release-lock.yaml,sha256sums.txt}`
- Modify: `docs/knowledge-base/99_manifest/{inventory.tsv,sha256sums.txt}`

**Steps:**

1. [ ] 在 `scripts/tests/test_knowledge_release.py` 添加配置读取、日期一致性、sealed mutation、activate-before-seal 测试；运行 `python3 -m unittest scripts.tests.test_knowledge_release`，预期新测试 FAIL。
2. [ ] 实现以下精确 CLI：`knowledge_release.py build --config <config>`、`seal --release <id>`、`verify --release <id>`、`activate --release <id>`；每个成功命令返回 0 并输出 `<action> <id>: PASS`。seal 后内容变化、seal 前 activate、日期不一致均返回非零。
3. [ ] 修改 reader rubric：可回答率 100%、必需来源链 100%、无依据正式事实 0、P1/P2 歧义 0；先写失败测试，再实现并运行 `python3 -m unittest scripts.tests.test_reader_rubric`。
4. [ ] 从 Task 4 manifest 解出 `<RELEASE_ID>` 并校验日期一致；构建 candidate，两次 clean rebuild 字节一致。
5. [ ] reader question schema 固定为 `question_id,prompt,required_source_ids,required_claims,required_uncertainty,prohibited_claims`；answer/result 固定为 `question_id,answer,source_ids,uncertainty,unsupported_claims,score,pass`。由未参与 Task 6 合成的独立 reviewer 在 sealed candidate 的 detached clean checkout 中作答，并写 `reader_id,independent_from_tasks:[5,6],attested_at`。
6. [ ] 独立审查必须 P1=0、P2=0；不允许一般性 waiver。通过后提交推送 sealed candidate。

构建、独立读者、封存命令合同（顺序固定，reader results 必须在 seal 前进入 lock）：

```bash
python3 scripts/documentation/knowledge_release.py build --config docs/knowledge-base/00_governance/releases/<RELEASE_ID>/release.yaml
git add --pathspec-from-file=<TASK_5_TO_7_DRAFT_PATHSPEC>
git commit -m 'docs: build <RELEASE_ID> draft candidate'
git worktree add --detach ../FLOW-reader-<RELEASE_ID> <DRAFT_CANDIDATE_SHA>
cd ../FLOW-reader-<RELEASE_ID>
python3 scripts/documentation/reader_rubric.py run \
  --questions docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/questions.yaml \
  --expected docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/expected.yaml \
  --rubric docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/rubric.yaml \
  --answers <INDEPENDENT_READER_ANSWERS> \
  --results docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/results.yaml \
  --reader-id <INDEPENDENT_READER_ID> \
  --attest-independent-from 5,6
cd <ORIGINAL_FLOW_WORKTREE>
python3 scripts/documentation/knowledge_release.py seal --release <RELEASE_ID>
python3 scripts/documentation/knowledge_release.py verify --release <RELEASE_ID>
```

`<TASK_5_TO_7_DRAFT_PATHSPEC>` 是从已批准 L2 change manifest 和本 Task 固定文件清单生成的 UTF-8/LF 路径文件，每行一个无通配符仓库相对路径，拒绝空行、tab/newline 文件名和仓库外路径；不允许 `git add .`。`<INDEPENDENT_READER_RESULTS>` 是 reviewer 返回的只读结果工件，回到原工作树后必须通过 `apply_patch` 写入固定 `results.yaml` 路径，再执行 seal。`reader_rubric.py run` 必须返回 0 并输出 `reader gate: PASS (answerable=100%, sources=100%, unsupported=0, p1=0, p2=0)`。seal 后不得再修改 questions/expected/rubric/results。

**Acceptance:** candidate sealed 且 `CURRENT_RELEASE` 仍为 `flow-knowledge-2026-09-12.1`。

### Task 8: 战略影响评估与用户正式裁决（S0–S1）

**Files:**
- Create: `docs/knowledge-base/04_decisions/<SNAPSHOT_DATE>-strategic-impact-assessment.md`
- Create: `docs/knowledge-base/04_decisions/<SNAPSHOT_DATE>-strategic-decision-proposal.md`
- Create: `docs/80_reviews/knowledge-refresh/<RELEASE_ID>/activation-file-manifest.tsv`

**Steps:**

1. [ ] 逐项对照 D052–D054、当前产品规格、路线图和 sealed candidate，形成 `keep/amend/add/remove/defer` 建议。
2. [ ] 每个建议写证据链、影响对象、替代方案、风险、迁移成本、验收标准；不得把 published-l2 写成 adopted-l3。
3. [ ] 运行 metadata、links、decision integrity；提交并推送 S0 文档。
4. [ ] 停止战略激活，向用户提交一组可一次性裁决的决定；记录逐项 accepted/amended/rejected/deferred。只有裁决后才进入 Task 9 新建正式 decision 文件。

**Acceptance:** 机器没有代替用户做产品目标和优先级决定；裁决记录可回溯 sealed candidate。

### Task 9: 暂存产品文档、路线图和阅读入口（S2–S3）

**Files:**
- Modify: `README.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Create: `docs/10_governance/decisions/D<next>--<user-approved-title>.md` (one per accepted/amended decision)
- Modify: `docs/10_governance/DECISION_INDEX.md`
- Create/Modify: `docs/10_governance/CHANGE_IMPACT_MAP.md`
- Modify: `docs/knowledge-base/07_handoff/HANDOFF.md`
- Modify: `HANDOFF.md`

**Steps:**

1. [ ] 用户裁决后先完成 `activation-file-manifest.tsv`：每个 S1 decision 一行或多行，列为 `decision_id,operation,path,evidence_refs,review_status`；列出确切 canonical product/architecture/roadmap 文件，禁止通配符和“相关文件”。用户确认的 accepted/amended 映射标为 `approved` 后才可编辑。
2. [ ] 只把 approved 行转成新的正式 decision 文件，以 `amends/supersedes` 连接 D052–D054；冻结的 `docs/knowledge-base/04_decisions/DECISION_LOG.md` 不得修改。rejected/deferred 留在提案历史。
3. [ ] 仅对清单中的确切路径统一项目目标、角色、证据/审核边界、模块可见性、路线图与验收。
4. [ ] 暂存但不单独提交激活差异；执行 FLOW 固定门禁命令。
5. [ ] 更新两个 HANDOFF；根 HANDOFF 记录项目状态/恢复，知识库 HANDOFF 记录 release/证据维护。

**Acceptance:** 所有 current 文档说法一致；没有未裁决 L2 内容被提升为 L3。

### Task 10: 原子激活、独立复验与三仓库收尾（K6 + V）

**Files:**
- Modify: `docs/knowledge-base/00_governance/releases/CURRENT_RELEASE`
- Modify: `README.md`
- Modify: `docs/00_start_here/PROJECT_STATE.md`
- Modify: `docs/00_start_here/READING_ORDER.md`
- Modify: `docs/10_governance/DECISION_INDEX.md`
- Create/Modify: `docs/10_governance/CHANGE_IMPACT_MAP.md`
- Modify: `docs/knowledge-base/07_handoff/HANDOFF.md`
- Modify: `HANDOFF.md`
- Create/Modify: only the additional exact canonical/decision paths marked `approved` in `docs/80_reviews/knowledge-refresh/<RELEASE_ID>/activation-file-manifest.tsv`
- Create: `docs/80_reviews/knowledge-refresh/<RELEASE_ID>/activation-verification.md`

The sealed directory `docs/knowledge-base/00_governance/releases/<RELEASE_ID>/` and sealed reader directory `docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/` are read-only in Task 10. The only release-state mutation is the external pointer `CURRENT_RELEASE`; any diff under either sealed directory aborts activation.

**Steps:**

1. [ ] 只暂存 activation 一致性集合，创建**尚未推送**的 commit A；记录 `ACTIVATION_SHA`。
2. [ ] 从 A 建 detached clean worktree，执行下列精确命令；全部返回 0，输出相应 PASS。先断言 `git diff <SEALED_CANDIDATE_SHA>..A -- docs/knowledge-base/00_governance/releases/<RELEASE_ID> docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>` 输出为空。将结果写到 sealed release **之外**的 `docs/80_reviews/knowledge-refresh/<RELEASE_ID>/activation-verification.md`，提交为 evidence commit E。
3. [ ] 从 E 的精确 `FINAL_SHA` 重新创建/重置 detached clean worktree，重复全部命令。第二轮不再修改任何跟踪文件；只有 E 被精确验证后才允许推送。
4. [ ] 推送 `FINAL_SHA` 并等待远端 CI；不强推。
5. [ ] 若远端 CI 失败，以正常新提交按 `git revert <E_SHA> <ACTIVATION_SHA>` 的顺序回退 evidence 和 activation（若 E 不含状态变更也保留审计记录并仅 revert A，必须在回退说明中明确）；恢复完整一致性集合并重跑同一门禁后推送。

精确复验命令：

```bash
git worktree add --detach ../FLOW-verify-<RELEASE_ID> <SHA>
cd ../FLOW-verify-<RELEASE_ID>
python3 scripts/documentation/source_baseline.py check-v2 \
  --snapshot-manifest <K2_ACCEPTED_MANIFEST> \
  --baseline docs/knowledge-base/10_sources/source-baseline-<SNAPSHOT_DATE>.tsv \
  --diff docs/knowledge-base/10_sources/source-diff-<SNAPSHOT_DATE>.tsv
python3 scripts/documentation/knowledge_release.py verify --release <RELEASE_ID>
python3 scripts/documentation/reader_rubric.py verify \
  --questions docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/questions.yaml \
  --expected docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/expected.yaml \
  --rubric docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/rubric.yaml \
  --results docs/knowledge-base/00_governance/reader-tests/<RELEASE_ID>/results.yaml
python3 scripts/documentation/coverage_validator.py \
  --coverage docs/knowledge-base/10_sources/coverage-<SNAPSHOT_DATE>.tsv \
  --exceptions docs/knowledge-base/10_sources/image-exceptions-<SNAPSHOT_DATE>.tsv \
  --change-manifest docs/knowledge-base/00_governance/change-manifests/<SNAPSHOT_ID>-l2.tsv \
  --strict
python3 scripts/check_docs.py --phase m6
python3 scripts/documentation/links.py --check
python3 scripts/documentation/kb_manifest.py --check
python3 -m unittest scripts.tests.test_decision_integrity
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
git status --porcelain=v1 --untracked-files=all
```

前九个验证命令须返回 0 并输出 PASS/OK；其中 reader 命令必须精确输出 `reader gate: PASS (answerable=100%, sources=100%, unsupported=0, p1=0, p2=0)`；最后一个 status 命令输出必须为空。复验记录至少包含 SHA、tree、运行者、开始/结束时间、逐命令返回码、输出 SHA-256 和结论。

**Acceptance:** 新 release、产品文档和路线图在同一 commit 生效；干净 checkout 与 CI 全绿；可回退到上一 release/commit。

## Execution Order and Stop Conditions

```text
Task 0 → Task 1 → Task 2/K0验收 → Task 3/K1写入
                                     ↓
                                Task 4 (首个稳定14:30/15:00/15:30)
                         ↓
Task 5 → Task 6 → Task 7 → Task 8/S0 → USER S1
                                          ↓ approved decisions only
                                      Task 9 → Task 10
```

- 15:00 截面失败不允许伪造替代；顺延期间可以继续改进工具，但不得构建正式新 baseline。
- 外部模型/API 不可用时保留 dry-run、coverage 和异常清单，不能把未处理项标完成。
- 用户未完成 S1 裁决时，执行停在 sealed candidate；这不是失败，而是设计中的人工控制点。
- 任一阶段发现敏感内容泄漏、上游树漂移或计数无法对账，立即停止下游发布并修复根因。
- HIGH 漏检率 >5%、任一知识域 MED/LOW 系统性误分、核心不可读 >1%、失败集中于单一来源/格式/主题，均阻断 K5 seal。
