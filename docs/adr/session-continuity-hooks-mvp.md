# Session Continuity Hooks — MVP 実装記録

**日付**: 2026-03-27  
**ステータス**: MVP 実装完了、動作確認待ち  
**ブランチ**: `feat/session-continuity-hooks`

---

## 概要

Copilot CLI / VS Code Claude の Hook 機構を利用して、セッション間の文脈断絶を防ぐシステムを実装した。

### 実装内容

| ファイル | 役割 |
|---|---|
| `.github/hooks/session-continuity.json` | hook 定義（`sessionStart` + `stop` イベント） |
| `.github/hooks/scripts/session-end.js` | events.jsonl → `.github/sessions/` に要約を保存 |
| `.github/hooks/scripts/session-start.js` | 前回セッション要約を `additionalContext` に注入 |
| `.github/hooks/scripts/lib/session-utils.js` | 共通ユーティリティ（JSONL パーサー、ファイル操作等） |
| `.github/sessions/` | セッション要約ファイルの保存先（tracked: NO） |

### 設計原則

- **冪等性**: Stop イベント複数発火時に何度走っても結果が同じ
- **非破壊**: ユーザー手書き領域（Notes, Context）は上書きしない
- **非ブロッキング**: hook 失敗時も常に `exit 0`
- **軽量**: transcript 全文ではなく要約のみ保存（ファイルサイズ抑制）

---

## 検証済み（commit 前確認）

### ✅ session-end.js

- 実在する `events.jsonl` から user.message を正しく抽出
- `tool.execution_start` から toolName およびファイル修正を抽出
- `apply_patch` テキストからパッチ内のファイルパスを正規表現で抽出
- 初回作成時は要約ブロック + Notes テンプレート生成
- 既存ファイル更新時は Summary マーカー内のみ冪等置換
- 2回実行で `Started` 保持、`Last Updated` のみ更新 ✓

### ✅ session-start.js

- `.github/sessions/` から最新セッションファイル（7日以内）を検索
- 雛形のままなら注入しない（実装済みの判定）
- stdout に JSON payload (`additionalContext`) を出力：
  ```json
  {
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": "Previous session summary:\n..."
    }
  }
  ```

### ✅ lib/session-utils.js

- Node.js 構文チェック OK
- JSONL パーサーが user.message / tool.execution_start を正しく判定
- git 情報取得（branch, root）が正常

---

## 残存リスク・未確認事項

### 1. Copilot Hook イベント対応（🔴 重要）

**現状**:
- `sessionStart` / `stop` イベントが Copilot で実装されているか未確認
- 確認済みは `preToolUse` のみ（既存 safety-guard.json）

**影響**:
- イベント未対応なら hook が実行されず、機能しない
- VS Code Copilot と Copilot CLI で異なる可能性

**対応予定**:
- 次回セッション開始時に stdout ログで hook 実行確認
- 未対応なら `preToolUse` で初回検出フォールバック実装

### 2. stdin JSON スキーマ不確定（🟡 中～低）

**仮定（実験的）**:
```json
{
  "sessionId": "UUID",
  "data": { "sessionId": "UUID" }
}
```

**検証方法**:
- 実際の hook 実行時に stderr ログで入力 JSON を記録
- schema に合わせて session-end.js の stdin 処理を調整

### 3. path normalization（🟡 低）

**現状**:
- Windows の `\` を `/` に正規化して git root 比較
- 大文字小文字も統一（toLowerCase）

**リスク**:
- 稀な edge case（symlink など）で誤マッチ可能性

---

## 次回セッション（別PC含む）でやること

### フェーズ 1: Hook 実行確認（セッション開始時）

```bash
# .github/sessions/ にセッションファイルが生成されているか確認
ls -la .github/sessions/

# 内容が正しく抽出されているか確認
head -30 .github/sessions/YYYY-MM-DD-*-session.md
```

期待値:
- `Session Summary` ブロック内に前回のタスク・ファイル一覧・ツール名
- `Last Updated` が現在時刻

### フェーズ 2: sessionStart context 注入確認（セッション開始時）

Copilot Chat で「前回のセッションを要約して」と言って、context が注入されているか確認。

期待値:
- Previous session summary が自動で提示される
- Notes for Next Session へのMentionが考慮される

### フェーズ 3: home-template への配備

確認後、以下を `home-template/.copilot/hooks/` へコピー:
- `session-continuity.json`
- `scripts/session-{end,start}.js`
- `scripts/lib/session-utils.js`

### フェーズ 4: repo-template への配備

確認後、以下を `repo-template/.github/hooks/` へコピー:
- session-continuity.json
- scripts/ 以下全て

---

## 不要な依存・最小化

- Node.js が `.copilot/` に自動付属（Copilot CLI インストール時）
- 外部 npm package なし（require() は `fs`, `path`, `child_process` のみ）
- `.claude/` フォルダ新規作成なし（既存 `~/.copilot/session-state/` を読み取り元）

---

## git 履歴

```bash
# atomic commit 候補
git add .github/hooks/session-continuity.json .github/hooks/scripts/
git add .github/sessions/.gitkeep
git add .gitignore  # lib/ → /lib/ 修正含む

git commit -m "feat(hooks): セッション継続機構 MVP

- session-end.js: events.jsonl を解析し .github/sessions/ に要約を保存
- session-start.js: 最新セッション要約を additionalContext に注入
- lib/session-utils.js: JSONL パーサー、ファイル操作、git 情報取得
- session-continuity.json: sessionStart / stop イベント定義

設計原則:
- 冪等: Stop 複数発火でも同じ結果
- 非破壊: Notes/Context 領域は上書きしない
- 非ブロッキング: hook 失敗時も exit 0

残存リスク: sessionStart/stop イベント Copilot 対応確認待ち
詳細は docs/adr/session-continuity-hooks-mvp.md を参照"
```

---

## 参考資料

- [仕様書（素案）](../local_references/session-continuity-spec.md) — 旧 ECC との比較、設計判断の根拠

