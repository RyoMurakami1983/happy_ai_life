# セッション共有を `docs/sessions/` に分離する

**日付**: 2026-04-02  
**ステータス**: 承認

---

## 背景

既存のセッション継続は `.github/sessions/` と `sessionStart/sessionEnd` hook で成立している。  
これは作業用の私的な継続には向くが、履歴として共有する文書には向かない。

今回ほしいのは、ユーザーがタイトルを確認し、公開配慮を通したうえで `docs/sessions/` に残す **共有用の成果物** である。

## 判断

- `.github/sessions/` は hook 管理の作業領域として維持する
- `docs/sessions/` を git-tracked の共有領域として新設する
- 共有文書の作成は `session-share-document` skill が担う
- `sessionStart` は `.github/sessions/` と `docs/sessions/` の両方を読めるようにする
- `sessionEnd` から share skill を自動起動することはしない

## 根拠

- hook は機械処理に向き、タイトル確認や公開配慮のような対話が必要な処理には向かない
- GitHub 公式の hook 仕様では、`sessionStart` / `sessionEnd` の出力はコンテキスト注入に使えず、hook から skill を直接起動する導線もない
- 共有文書は `knowledge-capture` の匿名化観点と整合させると安全
- 二層に分けることで、継続用データと共有用データの責務がぶれない

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| hook で直接共有文書を作る | 自動化しやすい | タイトル確認と公開配慮を飛ばしやすい |
| `furikaeri-practice` に統合する | 導線が短い | 共有と振り返りの責務が混ざる |
| **新規 skill + 二層構造** | 責務分離と公開配慮を両立できる | 共有は手動起動になる |

## 運用

- `furikaeri-practice` 完了後に共有したい場合は `session-share-document` を案内する
- `sessionStart` は最新の共有文脈を `session-context.instructions.md` に書き込む
- 共有文書は append-only とし、`YYYYMMDD-HHmmss_(Session名).md` で新規保存する
- 既存の `docs/sessions/*.md` 変更は repo-template の pre-commit hook で拒否する

## 状態

承認

