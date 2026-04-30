# 対話型ふりかえりを `furikaeri` に統合する

> **注記**: この ADR は既存リンクや履歴との互換性のため、ファイル名は旧名称の `session-share-document.md` のまま保持している。現在の判断主題は `session-share-document` の独立運用ではなく、`furikaeri` への統合である。

**日付**: 2026-04-02  
**ステータス**: 承認

> **現行補足**: 2026-04 の `session-continuity-retirement` により、`sessionStart` / `sessionEnd` hook を前提にした自動文脈注入は標準運用から封印した。`furikaeri` は home の `.copilot/docs/furikaeri/` を主保存先とする日次・横断ふりかえり workflow として継続し、repo 側の共有は必要な記録だけを明示的に残す。

---

## 背景

既存のセッション継続は `.github/sessions/` と `sessionStart/sessionEnd` hook で成立している。  
これは作業用の私的な継続には向くが、対話しながら学びを整理し、共有に耐えるふりかえりを残す体験としては不十分だった。

従来は `furikaeri` と `session-share-document` を分けていたが、保存が別入口になることでユーザーが置き去りになりやすかった。  
今回ほしいのは、セッションストーリーの確認から YWT / KPT の選択、SMART、必要時だけの skill 改善提案、保存までを 1 本の対話で完了できる workflow である。

## 判断

- `furikaeri` を単一入口とし、`session-share-document` は廃止する
- home の `.copilot/docs/furikaeri/` を共有ふりかえりの主保存先とし、repo 共有が必要な記録だけ `docs/furikaeri/` に残す
- `.github/sessions/` と `docs/sessions/` は repo 管理の標準保存先としては扱わない（既存履歴は保持してよい）
- `sessionStart` / `sessionEnd` による自動 continuity は標準運用から封印し、legacy repo の明示 opt-in に限定する
- `sessionEnd` の機械的 YWT ではなく、`furikaeri` による日次・横断ふりかえりを主導線にする

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
| **`furikaeri` に統合する** | 対話が切れず、保存まで迷いにくい | skill 本文と判断表の設計がやや重くなる |

## 運用

- `furikaeri` の中で、セッションストーリー確認 → YWT / KPT 分岐 → SMART → 保存まで進める
- 複雑な skill 利用や出戻りがある場合は YWT を出さず KPT に寄せる
- skill 改善提案は KPT 実施時にのみ候補化し、強化・カイゼンが望ましい場合だけ残す
- 公式 session data、必要に応じた `/chronicle standup`、明示的な `/share file session` を材料にする
- 保存時はまず home の `.copilot/docs/furikaeri/` に `YYYYMMDD-HHmmss-タイトル.md` で残し、repo 共有が必要な場合だけ `docs/furikaeri/` へ明示的に追加する

## 状態

承認
