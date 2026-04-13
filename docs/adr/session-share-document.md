# 対話型ふりかえりを `furikaeri-practice` に統合する

**日付**: 2026-04-02  
**ステータス**: 承認

---

## 背景

既存のセッション継続は `.github/sessions/` と `sessionStart/sessionEnd` hook で成立している。  
これは作業用の私的な継続には向くが、対話しながら学びを整理し、共有に耐えるふりかえりを残す体験としては不十分だった。

従来は `furikaeri-practice` と `session-share-document` を分けていたが、保存が別入口になることでユーザーが置き去りになりやすかった。  
今回ほしいのは、セッションストーリーの確認から YWT / KPT の選択、SMART、必要時だけの skill 改善提案、保存までを 1 本の対話で完了できる workflow である。

## 判断

- `.github/sessions/` は hook 管理の作業領域として維持する
- `furikaeri-practice` を単一入口とし、`session-share-document` は廃止する
- repo では `docs/furikaeri/`、home では `.copilot/docs/furikaeri/` を共有ふりかえりの保存先にする
- `sessionStart` は `.github/sessions/` と `docs/furikaeri/` の両方を読めるようにする
- `sessionEnd` は機械的 YWT を private log に残すだけにとどめ、対話型ふりかえりの代替にはしない

## 根拠

- hook は機械処理に向き、セッションストーリー確認や YWT / KPT の選択のような対話には向かない
- GitHub 公式の hook 仕様では、`sessionStart` / `sessionEnd` の出力はコンテキスト注入に使えず、hook から skill を直接起動する導線もない
- 共有文書は `knowledge-capture` の匿名化観点と整合させると安全
- private log と curated furikaeri を分けつつ、入口は 1 本にしたほうが UX と責務の両方を守れる

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| hook で直接共有文書を作る | 自動化しやすい | タイトル確認と公開配慮を飛ばしやすい |
| skill を 2 本維持する | 責務を分けやすい | 保存時にユーザーが置き去りになりやすい |
| **`furikaeri-practice` に統合する** | 対話が切れず、保存まで迷いにくい | skill 本文と判断表の設計がやや重くなる |

## 運用

- `furikaeri-practice` の中で、セッションストーリー確認 → YWT / KPT 分岐 → SMART → 保存まで進める
- 複雑な skill 利用や出戻りがある場合は YWT を出さず KPT に寄せる
- skill 改善提案は KPT 実施時にのみ候補化し、強化・カイゼンが望ましい場合だけ残す
- `sessionStart` は最新の共有文脈を `session-context.instructions.md` に書き込む
- 共有文書は append-only とし、`YYYYMMDD-HHmmss-タイトル.md` で新規保存する

## 状態

承認
