# happy-ai-life への再スコープと plugin split / skill slug 簡素化

**日付**: 2026-04-30
**ステータス**: 承認

## 背景

この母艦 repo は、変更前は `happy_ai_life_coding_Environment` という名前だったが、実体は当初から「AI と coding に閉じた環境」より広かった。
この repo はすでに、reusable skills / agents、trusted local bootstrap、repo bootstrap、safety guard、distribution metadata を扱う運用母艦になっている。

一方で、公開・共有向け distribution は `plugins/happy-ai-life/` の単一 plugin に集約されており、次の 2 つの問題があった。

1. **役割の混在**: 汎用 workflow / authoring / GitHub 運用 / office 系 asset と、仕様・設計・実装・デバッグ・言語別 setup のような coding 系 asset が同じ package に混在している。
2. **命名の冗長さ**: 一部の skill slug が長く、入口名としては冗長になっている。

今後 `happy-office` や `happy-play` のような拡張余地を残すには、まず `happy-ai-life` を umbrella concept として再定義し、その下の distribution boundary を整理する必要がある。

## 判断

### 1. repo の主旨を `happy-ai-life` に広げる

- この母艦 repo は「AI との楽しい coding 環境」に限定せず、**AI と続ける仕事・学習・創作の再利用可能な型を育てる母艦**として扱う。
- GitHub 上の実 repo slug / URL rename は、この ADR の判断後に `happy_ai_life` へ反映済みとする。

### 2. 公開・共有向け plugin は `happy-core` と `happy-coding` に分割する

公開・共有向け primary distribution は、単一の `happy-ai-life` plugin ではなく、次の 2 package を正本とする。

| plugin | 責務 |
|---|---|
| `plugins/happy-core/` | 汎用 workflow、知識化、振り返り、Git / GitHub 運用、Copilot asset authoring、office 系のような coding 非依存 asset |
| `plugins/happy-coding/` | 仕様、設計、実装、デバッグ、review、repo bootstrap、言語・技術別 setup、narrow coding agent |

- 旧 `plugins/happy-ai-life/` は transitional alias として残さず、未配布前提で完全置換する。
- marketplace manifest はこの 2 plugin を配布対象として持つ。
- `home-template/.copilot/` は引き続き trusted local bootstrap であり、plugin distribution の代替にはしない。

### 3. skill slug は plugin 名に引っ張らず、責務ベースで維持する

- skill 名は原則として **plugin prefix を付けず**、責務が明確な既存名は維持する。
- rename は「短くなっても意味が狭まりすぎない」ものに限定する。

今回採用する rename:

| 現在 | 新しい slug | 理由 |
|---|---|---|
| `furikaeri-practice` | `furikaeri` | 日本語で自然で、practice を省いても意図がぶれない |
| `git-commit-practices` | `git-commit` | entrypoint として十分に明快 |
| `gh-pr-workflow` | `gh-pr-create` | 実体が PR 作成・引き継ぎ中心であり、workflow より入口意図が見えやすい |
| `gh-pr-review-response` | `gh-pr-respond` | review する側ではなく、review に応答する側であることを残す |
| `gh-issue-intake` | `gh-issue-create` | backlog 化 / issue 化の入口であることを短く示す |

原則維持する代表例:

- `spec-workshop`
- `design-and-plan`
- `sdd`
- `debug`
- `safe-refactor`
- `modularity-review`

### 4. plugin 間の初期配置

初期の配布境界は次のとおりとする。

#### `happy-core`

- `copilot-authoring`
- `empirical-prompt-tuning`
- `furikaeri`
- `gh-issue-create`
- `gh-pr-create`
- `gh-pr-respond`
- `git-commit`
- `knowledge-capture`
- `pptx`
- `skill-eval`

#### `happy-coding`

- `debug`
- `deep-research-preflight`
- `deep-review-preflight`
- `design-and-plan`
- `dotnet*`
- `implement`
- `implementation-eval-gate`
- `modularity-review`
- `nuget-local`
- `python-setup-dev-environment`
- `repo-onboarding`
- `safe-refactor`
- `sdd`
- `spec-workshop`
- `typescript-*`
- narrow agent `tdd-coder`

`happy-office` や `happy-play` は将来の拡張候補であり、この ADR では追加しない。

### 5. 追補: authoring 入口の統合

後続整理で、公開 skill としての `skill` と `create-agents` は廃止し、必要な資産を `copilot-authoring` 配下の内部資産へ統合した。
現在の公開入口は `copilot-authoring` であり、skill authoring の資産は `plugins/happy-core/skills/copilot-authoring/_skill/`、agent authoring の資産は `plugins/happy-core/skills/copilot-authoring/_agent/` に置く。
一方、評価用の `skill-eval` と `empirical-prompt-tuning` は、authoring 入口とは別の評価 skill として維持する。

## 移行方針

1. まず ADR / README / instructions / marketplace metadata を更新する。
2. 次に plugin package を `happy-core` / `happy-coding` に分割する。
3. その後、rename 対象 skill の directory slug と参照を更新する。
4. 最後に tests / type-check / install guidance を揃える。

大きな構造変更と naming 変更を一度に行うが、**判断の正本はこの ADR** に固定し、以降の文書や package はそれに追従させる。

## 非目標

- GitHub 上の repo slug / repository URL の即時 rename
- `happy-office` / `happy-play` の同時実装
- plugin install に repo-local instructions / hooks / MCP config を含めること
- skill slug へ `core-` / `coding-` prefix を付与すること

## トレードオフ

- **利点**: plugin の install 判断が明確になり、将来の `office` / `play` 系の独立がしやすくなる。
- **利点**: skill slug が短くなり、対話中の入口名として使いやすくなる。
- **リスク**: plugin path と skill slug の変更により、docs / references / tests の追従漏れが起きやすい。
- **緩和策**: source of truth 文書と live package を優先して更新し、historical な session / furikaeri 記録は履歴として保持する。
