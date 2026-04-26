# Issue #82: Design Gap Detection and Emergency Fix

**Date**: 2026-04-27  
**Format**: KPT + 5 つのなぜ + Issue 化判定  
**Status**: 68 tests all PASS, production-ready

---

## Executive Summary

Issue #82（複数 repo 向け plan splitting）の 4-phase TDD を並列実装（52 tests ✅）後、Rubber-duck pre-review で「YAML schema mismatch」「checksum strategy undefined」「input validation missing」の 3 つの 🔴 BLOCKING ISSUES を検出。Emergency fix で 68 tests all PASS 到達。根本原因は「design-workshop で multi-repo data contract schema を明示しなかったこと」（設計フェーズ scope 不足）。

---

## Session Story

1. **4-phase TDD 背景実行**（tdd-coder agent）
   - Phase 1（split_multi_repo_plan sub-skill）: 10 tests ✅
   - Phase 2（SKILL.md updates: sdd / impl-and-ship / balanced-coupling-design）: 13 tests ✅
   - Phase 3（contract_verify checkpoint）: 8 tests ✅
   - Phase 4（fleet_orchestrator）: 21 tests ✅
   - **Cumulative: 52 tests all PASS**

2. **Rubber-duck 1st pre-review**（comprehensive critique）
   - 🔴 B1: YAML schema mismatch（Phase 1 生成 ↔ Phase 3/4 検証）
   - 🔴 B2: Checksum placeholder strategy undefined
   - 🔴 B3: Phase 4 入力検証欠落
   - 「do not merge」判定、2-4h 修正要求

3. **Emergency fix 並列実装**（3 agents）
   - Phase 1: schema field alignment
   - Phase 3: checksum persistence（plan.md に保存）
   - Phase 4: input validation + field name correction
   - **Result: 68 tests all PASS**

4. **Rubber-duck 2nd post-fix review**
   - YAML 生成ロジック（nested structure loss）は将来改善扱い
   - **Overall: production-ready 認定**

5. **ふりかえり & 根本原因分析**（5 つのなぜ）
   - ユーザー判定: Problem = 設計フェーズ（A）
   - **Root cause**: impl-and-ship の plan artifact spec に multi-repo schema がなかった
   - **Why chain**: spec なし → phase 独立 TDD → schema 不一致 → integration test で検出 → 実装後修正必須

---

## KPT

### Keep（継続すべき良い動き）

1. ✅ **Rubber-duck を実装前・実装後に 2 段階で走らせた**
   - 設計 issue を実装前に catch（設計修正の方が実装修正より低コスト）
   - 実装ロジック bug も実装後に catch
   - 「事前レビュー → 修正 → 再レビュー」の validation loop が機能

2. ✅ **4-phase TDD を粒度を揃えて並列実装した**
   - 各 phase が独立テスト可能 → integration で接続点検証
   - Emergency fix も 3 agents で迅速対応可能

3. ✅ **テスト駆動で Red-Green-Refactor を厳密に追跡**
   - 各 phase で failing test → green → refactor が明確
   - Schema 不一致も test で即座に検出可能

---

### Problem（改善すべき課題）

1. 🔴 **impl-and-ship の plan artifact spec が「single-repo 前提」のままだった**
   - Multi-repo data contract schema（YAML front-matter format）が明示されていない
   - Phase 1-4 が独立に schema 定義 → 不一致が発生
   - Design-workshop output に「data contract format」が含まれていなかった

2. 🟠 **Phase 1-4 の共通 schema 仕様に source of truth がなかった**
   - implementation-plan.md に散在 → unified spec ドキュメントなし
   - Integration test でも schema 一致を直接検証していなかった

3. 🟠 **AI-Slop 検出タイミングが実装後だった**
   - 「3 つの BLOCKING ISSUES」は設計段階で検出可能だった
   - Pre-review の scope が「logic」「type hints」に集中 → 「data contract」が外れていた

---

### Try（次セッション以降の改善）

#### **T1. impl-and-ship の plan artifact spec 拡張（優先・即実行）**

**What**: 
- `impl-and-ship/SKILL.md` の「plan.md schema」セクションを強化
- **single-repo schema** と **multi-repo schema** を明示的に分離
- YAML front-matter の「dependencies.contracts」を standardize：
  - `provides`: このリポが生産する artifacts
  - `requires`: このリポが消費する artifacts（上流依存）
  - `blocking`: 先に実行すべきリポ

**Why**: 
- 次の multi-repo feature 実装時に「schema mismatch」が起きない
- design-workshop の output checklist に「unified data contract spec」を追加できる

**How**: Issue 化 → 優先度 HIGH（design handoff に直結）

---

#### **T2. plan-schema validator skill は追加しない（シンプルイズベスト）**

**Decision**: ✅ Q1 確認済み → impl-and-ship の bootstrap phase に validation 統合で OK

**Effect**: 新規 skill overhead を避け、既存 skill 責務を明確化

---

### 5 つのなぜ（schema mismatch の根本原因）

| # | 問 | 答 | 
|---|---|---|
| 1 | なぜ schema mismatch が発生した？ | Phase 1-4 が独立に schema 定義したから |
| 2 | なぜ独立に定義した？ | phase ごとの TDD scope が「生成・検証ロジック」に限定され、「共通 format」が scope 外だったから |
| 3 | なぜ scope 外になった？ | implementation-plan.md で「unified schema spec」として分離されていなかったから |
| 4 | なぜ design で明示しなかった？ | design-workshop output の checklist に「data contract」が含まれていなかったから |
| 5 | なぜ checklist に入らなかった？ | impl-and-ship が「orchestration logic」中心に設計され、「data format standardization」が補助扱いだったから |

**Root cause**: design-workshop の「API / data flow」の粒度が「phase 間の handoff」まで達していなかった。

---

## SMART 目標

**S**: impl-and-ship/SKILL.md に「multi-repo plan schema」section を追加、phase 1-4 の YAML front-matter format を standardize する

**M**: 
- single-repo / multi-repo の schema を明示的に分離
- YAML front-matter の required fields を列挙
- Example を 2 件以上（single / multi）
- contract-verify checksum 方針も明示

**A**: 
- Issue #82 から抽出した YAML schema を反映
- design-workshop → impl-and-ship への handoff checklist に「unified data contract」を追加

**R**: 
- 次の multi-repo feature でも同じ schema を使用可能
- Integration test で schema 一致が事前に catch される

**T**: 
- Issue 化 → 次セッション or ASAP
- 実装: 30-45 min（schema doc + example）

---

## Issue 化候補

### **Issue A: impl-and-ship schema拡張（HIGH 優先度）**

**Title**: `design: impl-and-ship plan.md multi-repo schema を standardize`

**Description**:
```
Issue #82 implementation で設計 gap 検出。
Plan artifact spec が single-repo 前提のままで、
multi-repo data contract schema が明示されていない。

Emergency fix で 68 tests PASS したが、
設計段階での scope 不足が根因。

## What
impl-and-ship/SKILL.md に multi-repo schema section を追加：
- single-repo / multi-repo を明示分離
- YAML front-matter format を standardize（provides / requires / blocking）
- checksum strategy も明示

## Why
- 次の multi-repo feature 実装時に schema mismatch を防ぐ
- design-workshop の handoff checklist に「unified data contract」を追加できる

## Acceptance Criteria
- [ ] impl-and-ship/SKILL.md に schema section 追加
- [ ] single + multi の YAML example 各 1 件以上
- [ ] contract-verify checksum 方針を明示
- [ ] design-workshop handoff checklist に「data format」を追加
- [ ] Integration test for schema validation (optional: Phase 1-4)
```

---

## Suggested Next Steps

1. ✅ ふりかえり doc 作成（本ファイル）
2. ✅ doc commit + pull request
3. 🔄 **Issue A を GitHub 上で起票**（ユーザー or 自動）
4. 🔄 **Issue A 実装**（次セッション or ASAP）
   - impl-and-ship/SKILL.md 拡張
   - design-workshop handoff checklist 更新
5. 🔄 **PR review 対応** （GitHub Copilot agent）
6. 🔄 **main merge + branch cleanup**（ユーザーが VS Code で実施）

---

## Other Notes

- **Rubber-duck の価値**: 設計段階での problem detection で 2-4h の修正 cycle を実装前に catch。実装後修正は避けられなかったが、feedback loop を 2 ターンで完結できた。

- **AI-Slop 検出**: 「3 つの BLOCKING ISSUES」が実装段階で検出されたのは、design review scope が「logic」「type」に限定されていたこと。次の design review では「data contract / handoff format」を明示的に scope に含める。

- **シンプルイズベスト**: plan-schema validator skill を追加せず、impl-and-ship 内部 validation で対応。新規 skill overhead を避け、既存 skill 責務を明確化。

