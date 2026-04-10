---
name: furikaeri-practice
description: >
  セッション終了前のふりかえりを Quick（YWT）または Deep（KPT＋5つのなぜ）で進め、.github/sessions/ に保存する。前回の T（つぎにやること）を起点にセッションを繋ぐ。Use when: 作業の学びを整理したいとき、改善アクションを決めたいとき、「ふりかえり」と入力されたとき。
license: Personal
---

# ふりかえりプラクティス

セッションの学びを次の行動に変える router skill。既定は Quick（YWT）、問題や出戻りがあるときは Deep（KPT）へ切り替えます。Y は事実を厚めに、W は学びと詰まりをはっきり、T は次の一手と TRY を並べてよい形にします。

## こんなときに使う

- セッション終了前に学びを残したい（「ふりかえり」と入力）
- コーディングセッションや複数ターンの会話を閉じたい
- 詰まり・出戻り・再発があり、原因と対策を残したい
- 共有用の session 記録を docs/sessions に残したい

## 選び方

| 状況 | 使うもの | 目的 |
| --- | --- | --- |
| 日常の終了 | Quick（YWT） | 事実と学びを素早く整理して T に繋ぐ |
| 詰まり / 出戻り / 再発 | Deep（KPT） | Problem を分け、Try を実験に落とす |
| 共有文書を残す | session-share-document | Executive Summary 形式で archive に残す |

## ワークフロー

### Step 0 — 前回の T を確認する

前回セッションの T を見て、完了・継続・破棄を整理します。継続項目は今回の T に含めてよいです。

### Step 1 — Quick か Deep かを決める

- Quick: いつもの終了処理。YWT を軽く、でも具体的に。
- Deep: 問題が多い、同じ問題が再発する、根本原因が不明、環境改善の種を残したいとき。

### Step 2 — 出力を組み立てる

- Quick は **Y / W / T**。
- Deep は **Keep / Problem / Try / 5つのなぜ / SMART**。
- T は最大 3 件を目安にし、必要なら `TRY` を併記してよい。
- ふりかえり中に問題が見えたら、その場で Deep に切り替えてよい。

### Step 3 — 保存する

`.github/sessions/` に保存し、必要なら `session-share-document` で `docs/sessions/` 用の共有文書に整えます。

## 共通リソース

- `references/quick-ywt.md`
- `references/deep-kpt.md`
- `references/session-loop.md`
- `../session-share-document/`

## 注意点

- ふりかえりは報告書ではなく、次の改善に繋ぐ道具。
- Y を薄くしすぎると W/T の質が落ちる。
- Problem は人ではなく、プロセス・道具・条件に向ける。
- 環境や skill 自体の改善が見えたら、T に残して次の改善ループへ回す。
