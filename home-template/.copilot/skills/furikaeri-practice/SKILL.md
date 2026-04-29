---
name: furikaeri-practice
description: >
  セッションのふりかえりを対話で進め、セッションストーリーから YWT / KPT を選び、SMART 目標まで整えて repo の `docs/furikaeri/` と home の `.copilot/docs/furikaeri/` に保存する。KPT では必要に応じて skill 改善提案まで出す。Use when: 作業の学びを整理したいとき、改善アクションを決めたいとき、「ふりかえり」と入力されたとき。
license: Personal
---

# ふりかえりプラクティス

セッションの学びを次の行動と共有可能な記録に変える single-entry skill。まずセッションストーリーを対話でほどき、使った skill、出戻り、詰まりを確認してから YWT か KPT を選びます。軽い終了だけを Quick にし、複雑な流れや改善余地が見えるときは KPT に寄せます。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

- セッション終了前に学びを残したい（「ふりかえり」と入力）
- コーディングセッションや複数ターンの会話を閉じたい
- 詰まり・出戻り・再発があり、原因と対策を残したい
- 対話しながら repo / home のふりかえり記録まで保存したい

## 選び方

| 状況 | 進め方 | 目的 |
| --- | --- | --- |
| 作業が素直に進み、skill 利用も単純 | YWT | 事実と学びを素早く整理して SMART に繋ぐ |
| skill 利用が複雑 / 出戻りあり / 再発あり | KPT | Problem を分け、Try と SMART を明確にする |
| KPT で改善余地が見えた | KPT + 改善提案 | skill / hook / docs のカイゼン候補まで残す |

## ワークフロー

### Step 0 — 前回の T を確認する

前回セッションの T を見て、完了・継続・破棄を整理します。継続項目は今回の T に含めてよいです。

### Step 1 — セッションストーリーを展開する

- 何を進めたかを時系列で短くほどく
- 使った skill / hook / agent を確認する
- ユーザーの出戻り、詰まり、判断のやり直しがあったか確認する
- 複雑さが高ければ YWT を外し、KPT を主にする

### Step 2 — YWT か KPT かを決める

- YWT は「軽い終了」「複雑な skill 利用なし」「大きな出戻りなし」のときだけ使う
- KPT は「複雑」「出戻りあり」「改善余地が大きい」のいずれかで優先する
- 対話中に問題が見えたら、その場で KPT に切り替えてよい

### Step 3 — ふりかえりを組み立てる

- YWT は **Y / W / T / SMART** を作る
- KPT は **Keep / Problem / Try / 5つのなぜ / SMART** を作る
- ユーザーが Keep / Problem / Try を出したあと、アシスタント側でも補助候補を 1〜3 件だけ提示してよい
- 補助候補は「観測した摩擦」「言語化すると次回に効く良い動き」「未整理の改善種」を優先する
- skill 改善提案は KPT のときだけ候補にし、強化やカイゼンが望ましい場合にだけ書く

### Step 4 — 保存する

- `.github/sessions/` は hook が作る private continuity として扱い、これだけで完了扱いにしない
- 対話でタイトルと公開配慮を確認してから `docs/furikaeri/` に保存する
- 同じ basename で home の `.copilot/docs/furikaeri/` にも保存する
- 共有文書は append-only で残す

## 共通リソース

- `references/session-story.md`
- `references/quick-ywt.md`
- `references/deep-kpt.md`
- `references/output-shape.md`
- `references/naming.md`
- `references/session-loop.md`
- `../knowledge-capture/`

## 注意点

- ふりかえりは報告書ではなく、次の改善に繋ぐ道具。
- YWT を既定にしすぎない。複雑な session に Quick を当てると学びが痩せる。
- Problem は人ではなく、プロセス・道具・条件に向ける。
- 保存前に、モード・タイトル・公開配慮を対話で確認する。
