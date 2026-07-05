---
name: instructions-authoring
description: >
  repo-wide と path-specific の custom instructions を、責務分離と conflict 回避を保ちながら作成・改善する。
  `.github/copilot-instructions.md` や `.github/instructions/*.instructions.md` を新規作成したいとき、
  既存の rule を整理したいとき、instructions の境界を見直したいとき。
---

# Repository instructions を作成・改善する

この sub-skill は、repository custom instructions のうち **repo-wide** と **path-specific** だけを扱う入口です。`AGENTS.md` や home instructions まで広げない理由は、正本境界を狭く保ち、どの rule をどこに置くかを迷いにくくするためです。

## こんなときに使う

- `.github/copilot-instructions.md` を新しく整えたいとき
- `.github/instructions/*.instructions.md` を追加したいとき
- repo-wide と path-specific の責務分離を見直したいとき
- language rules や file-type rules の重複を減らしたいとき
- instructions の conflict や context 膨張を避けたいとき

## 判断表

| やりたいこと | 対象 | 次にやること |
| --- | --- | --- |
| repo 全体の事実と共通方針を書く | repo-wide | architecture、build/test、dispatch、完了条件のような repo 固有事実に絞る。 |
| 言語やファイル種別の局所 rule を追加する | path-specific | `applyTo` frontmatter を付け、対象ファイルだけに効く短い rule を書く。 |
| 既存 rule の重複や衝突を減らす | improve | repo-wide と path-specific の重複を削り、どちらか片方を正本に戻す。 |

## ワークフロー: instructions を進める

### ステップ 1 — 対象を repo-wide / path-specific に分ける

最初に、直したい guidance が repo 全体の事実なのか、特定パスに閉じた局所 rule なのかを分けます。ここが曖昧だと、常時読み込むべき情報と局所的にだけ効かせたい情報が混ざって、保守性が下がります。

### ステップ 2 — いちばん近い正本を選ぶ

- repo-wide: `.github/copilot-instructions.md`
- path-specific: `.github/instructions/*.instructions.md`

path-specific では frontmatter の `applyTo` を必ず付けます。複数の instructions が同時適用されると競合時の選択は non-deterministic なので、repo-wide と重なる guidance を安易に複製しません。

### ステップ 3 — 短い rule に圧縮する

instructions は常時コンテキストに入りやすいため、細かな手順や長い背景説明を詰め込みません。「常に守ってほしい短い rule」だけを残し、詳細 workflow は skill や README に逃がします。

### ステップ 4 — 周辺の導線を同期する

instructions の名前や役割が変わる場合は、README、関連 skill、dispatch 記述、template への参照も合わせて直します。入口だけ変えて周辺を古いまま残すと、利用者が古い guidance をたどって迷いやすくなるためです。

### ステップ 5 — checklist で review する

初期段階では validator を増やさず、次の checklist で確認します。

- repo-wide に language 固有ルールを書きすぎていないか
- path-specific に repo-wide の事実を重複させていないか
- `applyTo` が対象と一致しているか
- conflict しそうな rule が複数ファイルに分散していないか
- 秘密情報や個人依存パスを含んでいないか

## 早見表

| 対象 | 書くもの | 書かないもの |
| --- | --- | --- |
| repo-wide | architecture、build/test、dispatch、repo 固有事実 | 言語固有 style、長い手順、個人設定 |
| path-specific | 言語 / file type に閉じた short rule | repo-wide の繰り返し、dispatch、詳細 workflow |

## 共通リソース

- `../../../../../docs/adr/instruction-hierarchy-and-authoritative-source.md` — instruction の正本と precedence
- `../../../../../.github/copilot-instructions.md` — repo-wide の現行正本
- `../../../../../repo-template/.github/instructions/` — path-specific instructions の配布テンプレート
- `../improve-existing/` — guidance 改善の共通フロー

## 注意点

- **scope を広げすぎない**: home instructions や `AGENTS.md` まで一緒に触ると、正本境界が崩れます。
- **conflict を precedence で解決しようとしない**: repo-wide と path-specific の競合は不安定なので、重複そのものを避けます。
- **instructions を手順書にしない**: 長い workflow は skill に置いたほうが、常駐 context を圧迫しません。
