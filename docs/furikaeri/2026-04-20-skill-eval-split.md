# ふりかえり: skill-eval 分離 & empirical-prompt-tuning 統合

**日時:** 2026-04-20  
**セッション:** skill-eval 分離計画と初期実装（1 セッション）  
**成果物:** PR #75 - skill-eval router + empirical-prompt-tuning 新規追加 + behavioral assets 移動  
**テスト:** 70 passed, 3 skipped ✅  

---

## セッションストーリー

1. **計画フェーズ（sdd + rubber-duck）**
   - 分離スコープを定義（eval behavioral / validate static 分離）
   - rubber-duck で blocking issue 発見：run_loop.py が validate_skill.py に同居前提
   - 計画修正：移動不可ファイルと移動ファイルを明確に分類

2. **実装フェーズ（5 フェーズ）**
   - P1: empirical-prompt-tuning SKILL.md 新規作成
   - P2: skill-eval router + sub_skills (benchmark / empirical) 作成
   - P3: behavioral eval assets 移動（agents / schemas / scripts / tests / eval_review.html）
   - P4: 既存 skill 参照更新（skill/evaluate 委譲ポインター化、validate/improve/copilot-authoring 参照更新）
   - P5: テスト・検証・polish

3. **Polish フェーズ**
   - empirical-prompt-tuning の R2/R8 修正（validator warn → L2 Recommended 10/10）
   - 全テスト通過確認

4. **PR・クローズ**
   - PR #75 作成・push 完了

---

## KPT

### Keep（続ける・大事にする）

- **計画後の粒度の良いタスク分解**：SQL todos テーブルに 5 フェーズ × 3 粒度で 15 タスク + 依存関係を登録。実装中に「何をするか」が明確。
- **rubber-duck の高速発見性**：計画直後に blocking issue（run_loop.py 依存）を指摘。パッチ当てでなく設計修正に繋いだ。
- **フェーズ分割の実効性**：1 フェーズ 1 テーマで進行。各フェーズの完了確認が単純。

### Problem

- 特になし。計画で依存関係を明確にしたため、実装の出戻りなし。

### Try

- **plan.md → SQL todos 生成の仕組み化**
  - 現状：plan.md の TODO を手書き SQL INSERT
  - 提案：sdd skill のワークフロー に「task 登録ステップ」追加。plan artifact から todos テーブルへの落とし込みを自動化／テンプレート化
  - 効果：同じスコープ・フェーズ規模の計画で再利用可能

---

## SMART 目標（2 次セッション以降の action）

**Goal:** sdd skill に task 登録ステップを追加し、plan → todos 生成を仕組み化

**Specific:**
- sdd のワークフロー Step 3 or 4 に「task テーブル登録」を追加
- plan.md の TODO セクションから SQL INSERT statement を生成するか、template を提供
- 既存 todos テーブル schema（id, title, description, status, todo_deps）を確認

**Measurable:**
- 次の計画型セッションで「plan.md → SQL」の手作業が 5 分以下に短縮できたか

**Achievable:**
- sdd skill は既に存在。dependencies, phasing の概念も既定
- template or 簡易 generator で対応可能

**Relevant:**
- 複数フェーズ計画が重いほど効果が高い
- 他の skill（design-workshop, impl-and-ship 等）にも波及可能

**Time-bound:**
- 目標：次の計画型セッション以前に実装

---

## 副産物 / 学び

1. **blocking issue の早期発見の重要性**
   - validate_skill.py は validate / improve / copilot-authoring など多数の skill から参照
   - run_loop.py も validate_skill.py に同居前提
   - 事前に依存グラフを把握していた rubber-duck が、移動不可の正当な理由を指摘

2. **テンプレート assets の管理**
   - eval_review.html は generate_viewer.py から `parents[1].parent / "assets"` で参照
   - 移動時にパスが自動で解決される（相対参照のメリット）

3. **引き伝い性と検証**
   - L1/L2 validator pass で新規 skill の基本形が保証される
   - empirical-prompt-tuning の polish（R2/R8 修正）は validator feedback に従うだけで自動実装

---

## 記録情報

- **ファイル:** `docs/furikaeri/2026-04-20-skill-eval-split.md`（公開）
- **PR:** #75
- **Branch:** feat/split-skill-eval
- **Next session:** sdd skill に task 登録ステップ追加（SMART 参照）
