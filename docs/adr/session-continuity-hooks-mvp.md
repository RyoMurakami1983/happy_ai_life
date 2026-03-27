# Session Continuity Hooks — MVP 実装記録

**日付**: 2026-03-27  
**ステータス**: MVP 実装完了、公式仕様適合済み、テンプレート配備済み  
**ブランチ**: `feat/session-continuity-hooks`

---

## 概要

Copilot CLI / VS Code の Hook 機構を利用して、セッション間の文脈断絶を防ぐシステムを実装した。

### 実装内容

| ファイル | 役割 |
|---|---|
| `.github/hooks/session-continuity.json` | hook 定義（`sessionStart` + `sessionEnd` イベント） |
| `.github/hooks/scripts/session-end.js` | events.jsonl → `.github/sessions/` に要約を保存 |
| `.github/hooks/scripts/session-start.js` | 前回セッション要約を `.github/instructions/` に書き出し |
| `.github/hooks/scripts/lib/session-utils.js` | 共通ユーティリティ（JSONL パーサー、ファイル操作等） |
| `.github/sessions/` | セッション要約ファイルの保存先（tracked: NO） |
| `.github/instructions/session-context.instructions.md` | 自動生成コンテキスト（tracked: NO） |

### 設計原則

- **冪等性**: sessionEnd イベント複数発火時に何度走っても結果が同じ
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
- 公式 sessionEnd スキーマ `{ timestamp, cwd, reason }` に適合 ✓
- `reason` フィールドをメタデータに追加 ✓

### ✅ session-start.js

- `.github/sessions/` から最新セッションファイル（7日以内）を検索
- 雛形のままなら注入しない（実装済みの判定）
- `.github/instructions/session-context.instructions.md` にファイル書き出し ✓
- セッションなし or 雛形のみの場合はファイルを削除（残存コンテキスト防止） ✓
- `applyTo: "**"` 付き instructions.md フォーマットで出力 ✓

### ✅ lib/session-utils.js

- Node.js 構文チェック OK
- JSONL パーサーが user.message / tool.execution_start を正しく判定
- git 情報取得（branch, root）が正常

---

## 解決済みリスク

### 1. ~~Copilot Hook イベント対応~~ ✅ 解決

**問題**: `stop` イベントが公式仕様にない
**解決**: 公式リファレンス確認により `sessionEnd` が正しいイベント名と判明。修正済み。

公式サポートイベント一覧（[Hooks Configuration Reference](https://docs.github.com/en/copilot/reference/hooks-configuration)）:
- `sessionStart` / `sessionEnd` / `userPromptSubmitted`
- `preToolUse` / `postToolUse` / `errorOccurred`

**VS Code 互換性**: VS Code Copilot も同じ `.github/hooks/` を読むため、両環境で動作。

### 2. ~~stdin JSON スキーマ不確定~~ ✅ 解決

**公式スキーマ（確定）**:

sessionEnd 入力:
```json
{
  "timestamp": 1704618000000,
  "cwd": "/path/to/project",
  "reason": "complete"
}
```

sessionStart 入力:
```json
{
  "timestamp": 1704614400000,
  "cwd": "/path/to/project",
  "source": "new",
  "initialPrompt": "Create a new feature"
}
```

**注意**: `sessionId` は stdin に含まれない。events.jsonl の探索は cwd ベースのマッチングで対応。

### 3. ~~sessionStart の stdout 出力~~ ✅ 設計変更で解決

**問題**: 公式ドキュメントで sessionStart の Output は "Ignored" と明記されており、`additionalContext` 注入が機能しない。

**解決**: stdout 出力方式を廃止し、`.github/instructions/session-context.instructions.md` へのファイル書き出し方式に変更。Copilot は `.github/instructions/**/*.instructions.md` を自動的にコンテキストとして読み込むため、前回セッションの要約が自然に注入される。

### 4. path normalization（🟡 低 — 残存）

**現状**:
- Windows の `\` を `/` に正規化して git root 比較
- 大文字小文字も統一（toLowerCase）

**リスク**:
- 稀な edge case（symlink など）で誤マッチ可能性

---

## テンプレート配備状況

### ✅ フェーズ 3: home-template への配備

以下を `home-template/.copilot/hooks/` に配備済み:

| ファイル | 備考 |
|---|---|
| `session-continuity.json` | `$HOME/.copilot/hooks/scripts/` パスに調整 |
| `scripts/session-start.js` | 本体と同一 |
| `scripts/session-end.js` | 本体と同一 |
| `scripts/lib/session-utils.js` | 本体と同一 |

### ✅ フェーズ 4: repo-template への配備

以下を `repo-template/.github/hooks/` に配備済み:

| ファイル | 備考 |
|---|---|
| `session-continuity.json` | `.github/hooks/scripts/` 相対パス |
| `scripts/session-start.js` | 本体と同一 |
| `scripts/session-end.js` | 本体と同一 |
| `scripts/lib/session-utils.js` | 本体と同一 |

---

## 次回セッションでやること

### フェーズ 5: 実地動作確認

```bash
# セッション終了後に .github/sessions/ にファイルが生成されているか確認
ls -la .github/sessions/

# 内容が正しく抽出されているか確認
head -30 .github/sessions/YYYY-MM-DD-*-session.md
```

期待値:
- `Session Summary` ブロック内に前回のタスク・ファイル一覧・ツール名
- `Last Updated` が現在時刻

### フェーズ 6: sessionStart context 注入確認

次回セッション開始時に `.github/instructions/session-context.instructions.md` が生成されるか確認。

```bash
cat .github/instructions/session-context.instructions.md
```

期待値:
- `applyTo: "**"` 付きの instructions.md フォーマット
- 前回セッションの要約が含まれる
- Copilot が自動的にコンテキストとして認識する

---

## 不要な依存・最小化

- Node.js が `.copilot/` に自動付属（Copilot CLI インストール時）
- 外部 npm package なし（require() は `fs`, `path`, `child_process` のみ）
- `.claude/` フォルダ新規作成なし（既存 `~/.copilot/session-state/` を読み取り元）

---

## 参考資料

- [仕様書（素案）](../local_references/session-continuity-spec.md) — 旧 ECC との比較、設計判断の根拠
- [Hooks Configuration Reference](https://docs.github.com/en/copilot/reference/hooks-configuration) — 公式 hook イベント仕様

