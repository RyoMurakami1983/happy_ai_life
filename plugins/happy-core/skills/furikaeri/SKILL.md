---
name: furikaeri
description: >
  セッションまたは 1 日のふりかえりを対話で進め、セッションストーリーから YWT / KPT を選び、SMART 目標まで整えて home の `.copilot/docs/furikaeri/` を主保存先に残す。必要に応じて repo の `docs/furikaeri/` にも共有保存する。KPT では必要に応じて skill 改善提案まで出す。Use when: 作業の学びを整理したいとき、改善アクションを決めたいとき、「ふりかえり」と入力されたとき、1 日の終わりに複数 repo の作業をまとめたいとき。
license: Personal
---

# ふりかえりプラクティス

セッションまたは 1 日の学びを次の行動と共有可能な記録に変える single-entry skill。まずセッションストーリーを対話でほどき、使った skill、出戻り、詰まりを確認してから YWT か KPT を選びます。軽い終了だけを Quick にし、複雑な流れや改善余地が見えるときは KPT に寄せます。
ゴール駆動で使うため、最初に達成したいゴール、成功条件、確認手段を短く固定します。


## こんなときに使う

- セッション終了前に学びを残したい（「ふりかえり」と入力）
- 1 日の終わりに、複数 repo / 複数 session の作業を 1 つの日次ふりかえりへまとめたい
- コーディングセッションや複数ターンの会話を閉じたい
- 詰まり・出戻り・再発があり、原因と対策を残したい
- 対話しながら home のふりかえり記録と、必要な repo への共有記録まで保存したい

## 判断表

| 状況 | 進め方 | 目的 |
| --- | --- | --- |
| 作業が素直に進み、skill 利用も単純 | YWT | 事実と学びを素早く整理して SMART に繋ぐ |
| skill 利用が複雑 / 出戻りあり / 再発あり | KPT | Problem を分け、Try と SMART を明確にする |
| 1 日の終わりに複数 repo をまとめる | Daily KPT / YWT | `~/.copilot/docs/furikaeri/` に横断記録を残す |
| KPT で改善余地が見えた | KPT + 改善提案 | skill / hook / docs のカイゼン候補まで残す |

## ワークフロー

### Step 0 — 前回の T を確認する

前回セッションの T を見て、完了・継続・破棄を整理します。継続項目は今回の T に含めてよいです。

日次ふりかえりの場合は、公式 session data を source of truth として扱います。`/chronicle standup for today` が使える環境ではその出力を材料にし、experimental が使えない場合は今回の session story と必要に応じた `/share file session [PATH]` の明示 export を材料にします。

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

- `sessionStart` / `sessionEnd` による repo-local 自動保存は標準運用から封印済みとして扱い、これだけで完了扱いにしない
- 対話でタイトルと公開配慮を確認してから、まず home の `.copilot/docs/furikaeri/` に保存する
- repo へ共有すべき内容だけ、同じ basename で `docs/furikaeri/` にも保存する
- 共有文書は append-only で残す
- `/share gist` は明示依頼がある場合だけ使い、既定は local file 保存にする

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
- `/chronicle` は experimental なので、使えない場合の fallback を必ず用意する。
- session data は local に保存されるが、要約に使うと関連内容が通常の Copilot 応答と同様に model へ送られる可能性がある。secret や非公開情報は保存・共有前に必ず確認する。
