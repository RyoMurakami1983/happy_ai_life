# Skill Ecosystem Action Plan

## 目的

この文書は、`happy_ai_life` の skill / agent / privateEval / docs を、シンプルで保守しやすい skill ecosystem として育てるための実行計画です。

参考にしたのは Matt Pocock さんの `skills` repo の構造と運用です。ただし内容の移植ではなく、次の設計パターンだけを抽出して、この repo の配布境界へ合わせます。

- 小さく、組み合わせやすい skill
- `CONTEXT.md` によるドメイン語彙の濃縮
- 基本 skill から専門 skill へつながる地図
- 評価を後付けにせず、skill を育てる仕組みに入れる

この文書の最初の着手点は、末尾の「最初のPR候補」です。P0-P3 は全体バックログ、段階導入は順序の根拠として扱います。

## Source of truth

| 領域 | 正本 |
| --- | --- |
| 公開配布される plugin | `plugins/happy-core/`, `plugins/happy-coding/` |
| plugin metadata | `plugins/*/plugin.json`、`.github/plugin/marketplace.json` は mirror |
| home bootstrap | `home-template/.copilot/` と `scripts/sync_to_home_cli.py` |
| downstream repo template | `repo-template/` |
| 試作・昇格前 | `works/` |
| 品質ゲート | `docs/QUALITY_GATES.md`, `.github/workflows/quality.yml` |
| 設計判断 | `docs/adr/` |

## 4視点の結論

| 視点 | 主要な結論 |
| --- | --- |
| 参考 repo 分析 | `domain-modeling`、router skill、短い `SKILL.md`、progressive disclosure を取り入れる価値が高い。npm / symlink / changeset 運用はこの repo には持ち込まない。 |
| ローカル構造 | `grill-with-docs -> design-and-plan -> implement` の流れは既にあるが、skill 依存、works 昇格基準、plugin README 共通事項、version 整合の確認が弱い。 |
| privateEval | `evals/<skill-id>/` を repo 内の secret なし評価ケース置き場にする。raw log、実会話、秘密情報は repo に入れない。 |
| 保守性・性能 | 40本前後の skill は地図なしでは探索コストが高い。評価語彙の分岐、長い docs / SKILL.md、stale 参照が長期的な速度低下につながる。 |

## 採用するパターン

### 1. 基本 skill を入口にする

`happy-coding` は、次の基本 skill を上位入口として扱います。

```text
grill-with-docs
  -> design-and-plan
    -> implement
      -> implementation-eval-gate
        -> deep-review-preflight
```

専門 skill は、この流れを置き換えず、必要な場面だけ接続します。

例:

```text
design-and-plan
  -> modularity-review
  -> dotnet
  -> prototype

implement
  -> safe-refactor
  -> debug
  -> happy-coding:tdd-coder
```

### 2. `CONTEXT.md` を純粋な用語集として使う

`docs/PHILOSOPHY.md` は価値観と背景の正本です。一方、日常の skill 実行で毎回読むには重いため、ドメイン語彙だけを `CONTEXT.md` に切り出します。

入れるもの:

- canonical term
- 避ける別名
- 1-2文の定義
- 所有関係や範囲が重要な場合の最小説明

入れないもの:

- 仕様詳細
- 設計メモ
- 実装方針
- TODO
- 一般的な技術語

初期候補:

| 用語 | 意味の方向性 |
| --- | --- |
| skill | `SKILL.md` で定義された、AI agent の再利用可能な手順・判断基準 |
| plugin | `plugin.json`、`skills/`、`agents/` を含む Copilot CLI 配布単位 |
| works | 常用・配布前の試作置き場 |
| privateEval | secret なしの評価ケースで skill 品質を継続的に測る仕組み |
| 型 | 再現可能な仕事の進め方。自由を奪うテンプレートではなく、速度と安全の土台 |
| 余白 | 変更、学習、回復のために意図して残す時間・設計上の空き |

### 3. `SKILL.md` は短くし、詳細は `references/` へ逃がす

`SKILL.md` は常時読まれる可能性があるため、判断と流れに絞ります。長い説明、例、チェックリストは `references/` や `sub_skills/` に置きます。

目安:

- `SKILL.md`: 入口、使う場面、core loop、成功条件
- `references/`: 書式、詳細ルール、背景、例
- `sub_skills/`: 分岐した実行手順

### 4. privateEval を `skill-eval` の下に接続する

`privateEval` は新しい第三の評価体系ではなく、`skill-eval` と `loop-engineering` の Evaluate を具体化する評価ケース群として扱います。

repo に入れてよいもの:

- `evals/<skill-id>/evals.json`
- secret を含まない期待結果
- 集計済みの benchmark summary
- append-only の benchmark history

repo に入れないもの:

- 実会話ログ
- 個人情報
- API key、token、認証情報
- private repo のコード片
- 顧客・職場・未公開情報を推測できる内容

## 採用しないパターン

| パターン | 採用しない理由 |
| --- | --- |
| npm / changeset 前提の配布 | この repo は Copilot CLI plugin と Python / uv の運用が中心。plugin version 管理と marketplace metadata で十分。 |
| symlink による skill 配布 | Windows での管理コストが高い。既存の home sync / plugin install を優先する。 |
| 参考 repo の skill 本文の移植 | 著作権・文脈差分・保守責任の観点から、構造だけを参考にする。 |
| 全 skill の常時 full eval | 開発速度を落とす。P0/P1 skill と変更影響範囲に絞って育てる。 |
| スタック特化 skill の無制限追加 | 基本 skill の地図から外れた skill が増えると探索速度が落ちる。まず router / 地図へ接続できるか確認する。 |

## 実行アクション

### P0: 入口と正本を固定する

P0 は最初のPRにすべて入れる作業ではありません。skill ecosystem の土台として、早い段階で順に解消する全体バックログです。

| Action | 変更候補 | Acceptance check |
| --- | --- | --- |
| Skill map を作る | `docs/SKILL_MAP.md` | `plugins/happy-core/skills/*/SKILL.md` と `plugins/happy-coding/skills/*/SKILL.md` の全 skill が1回ずつ列挙され、存在しない skill 名を含まない。 |
| privateEval の置き場を作る | `evals/<skill-id>/` | 最初の5 skill に happy path / near-miss / failure の3ケースがある。 |
| 評価語彙を統一する | `docs/QUALITY_GATES.md`, `plugins/happy-core/skills/skill-eval/SKILL.md` | `skill-eval`、`empirical-prompt-tuning`、`loop-engineering`、privateEval の入口、対象、実行タイミングが1表にまとまっている。 |
| secret 非混入ルールを明文化する | `docs/QUALITY_GATES.md` または `docs/PRIVATE_EVAL.md` | raw log と実会話を repo に入れないことが明記されている。 |
| privateEval raw artifact を除外する | `.gitignore`, `docs/PRIVATE_EVAL.md` | raw log / 実会話 / viewer 出力の保存先が repo 外または git ignore 対象として明記されている。 |

最初に eval を作る skill:

1. `copilot-authoring`
2. `skill-eval`
3. `grill-with-docs`
4. `design-and-plan`
5. `implementation-eval-gate`

### P1: ドメイン知識を濃縮する

| Action | 変更候補 | Acceptance check |
| --- | --- | --- |
| root `CONTEXT.md` を作る | `CONTEXT.md` | `skill`、`plugin`、`works`、`privateEval`、`型`、`余白` が1-2文で定義されている。 |
| `domain-modeling` 相当を作る | `plugins/happy-core/skills/domain-modeling/SKILL.md` | `grill-with-docs` から用語解決時に参照できる。 |
| `AUTHORING.md` に skill 作成規律を足す | `docs/AUTHORING.md` | leading word、no-op pruning、completion criterion、progressive disclosure の4項目が見出し付きで説明されている。 |
| `SKILL.md` の長文化を抑える | `docs/AUTHORING.md` と focused check | 長い詳細は `references/` へ移す方針と、例外時の理由を残す方針が書かれている。 |

### P2: 保守性の穴を塞ぐ

| Action | 変更候補 | Acceptance check |
| --- | --- | --- |
| plugin README 共通部分を DRY 化する | `docs/PLUGIN_MAINTENANCE.md`, `plugins/*/README.md` | version 更新、local marketplace add、更新通知方針が1箇所から参照される。 |
| plugin version sync test を追加する | `tests/test_plugin_manifest.py` | `plugins/*/plugin.json` と `.github/plugin/marketplace.json` の version ずれを検出する。 |
| works 昇格基準を作る | `docs/WORKS_PROMOTION.md` | works から `happy-core` / `happy-coding` へ昇格する条件と確認者が明記される。 |
| skill 依存を明示する | `docs/AUTHORING.md`, 中核 `SKILL.md` | `grill-with-docs -> design-and-plan -> implement` の前提と handoff 条件が読める。 |
| stale 参照を検出する | docs link smoke test | 存在しない skill 名・path 参照を検出できる。 |
| evals の secret / PII smoke を追加する | tests または quality script | `evals/` 配下に token らしき値、実会話ログ名、raw artifact 名が混入した場合に検出できる。 |

### P3: 読む量と過去判断を整理する

| Action | 変更候補 | Acceptance check |
| --- | --- | --- |
| `PHILOSOPHY.md` を二層化する | `docs/PHILOSOPHY.md` と詳細 references | 常時読む要約が1スクロールに収まり、詳細へリンクされる。 |
| ADR status を揃える | `docs/adr/*.md` | 全 ADR に `Status: Accepted / Superseded / Retired` がある。 |
| numbered docs の index を作る | `docs/grill_results/README.md` など | active / superseded が区別できる。 |
| router skill を作る | `plugins/happy-core/skills/ask-happy/SKILL.md` または `happy-coding` | user-invoked skill が増えても入口が1つになる。 |

## privateEval の最小カタログ

| Catalog | 測るもの | 最小ケース |
| --- | --- | --- |
| routing | どの skill が呼ばれるべきか | should-trigger / near-miss / should-not-trigger |
| handoff | 次工程が迷わず続けられるか | grill result、plan、implementation contract |
| source of truth | README、docs、ADR、plugin manifest に戻れているか | 正本あり / 正本衝突 / 正本なし |
| implementation | acceptance check まで到達できるか | small slice / missing test / blocked case |
| safety | secret、hook bypass、破壊的操作を誘導しないか | reject / ask / safe alternative |
| docs-reader | 初見読者が目的・手順・判断基準を理解できるか | README reader / maintainer reader / AI reader |
| cost | tool 回数、再試行、往復が増えていないか | baseline / changed / regression |

## 段階導入

1. **地図を作る**: `docs/SKILL_MAP.md` で基本 skill と専門 skill の関係を固定する。
2. **評価の正本を作る**: `evals/<skill-id>/` を1 skill から始め、5 skill まで広げる。
3. **用語を濃縮する**: root `CONTEXT.md` を作り、`PHILOSOPHY.md` から日常語彙を抽出する。
4. **作成規律を文書化する**: `AUTHORING.md` に pruning と completion criterion を足す。
5. **保守ゲートを追加する**: version sync test、stale 参照検出、docs link smoke を追加する。
6. **棚卸しする**: 地図に乗らない skill、重複 skill、古い ADR を整理する。

## やらないこと

- `plugins/happy-core/` と `plugins/happy-coding/` 以外に、新しい常用 plugin を増やすことを前提にしない。
- `works/` の成果物を、昇格基準なしに plugin へ移さない。
- AI 評価で機械テストを置き換えない。
- privateEval に実会話や秘密情報を入れない。
- すべての変更に重い review / full eval を強制しない。

## 最初のPR候補

最初のPRは、実装範囲を広げすぎず、次の3点に絞るのが安全です。

1. `docs/SKILL_MAP.md` を作る。
2. `docs/PRIVATE_EVAL.md` または `docs/QUALITY_GATES.md` に privateEval の置き場と禁止事項を書く。
3. `docs/AUTHORING.md` に `SKILL.md` pruning と handoff / dependency の最小規律を足す。

このPRでは `evals/<skill-id>/` の本格実体化までは行いません。禁止事項、配置方針、除外すべき raw artifact を先に固定し、次の PR で `CONTEXT.md`、`domain-modeling`、最初の `evals/<skill-id>/` へ進みます。

## 参考

- Matt Pocock skills: <https://github.com/mattpocock/skills/tree/main>
- `docs/PHILOSOPHY.md`
- `docs/DEVELOPMENT.md`
- `docs/AUTHORING.md`
- `docs/QUALITY_GATES.md`
- `docs/grill_results/001_GRILL_WITH_DOCS_RESULT.md`
- `plugins/happy-core/skills/skill-eval/SKILL.md`
- `plugins/happy-core/skills/loop-engineering/SKILL.md`
- `plugins/happy-coding/skills/grill-with-docs/SKILL.md`
- `plugins/happy-coding/skills/design-and-plan/SKILL.md`
- `plugins/happy-coding/skills/implement/SKILL.md`
