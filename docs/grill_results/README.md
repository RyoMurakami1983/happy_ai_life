# Grill Results

このディレクトリは、`grill-with-docs` の結果を保存する場所です。
各ファイルは同じ案件の design / plan と番号を共有できます。

| File | Status | Topic |
| --- | --- | --- |
| [001_GRILL_WITH_DOCS_RESULT.md](001_GRILL_WITH_DOCS_RESULT.md) | active | Loop Engineering と PrivateEval の `happy-core` 配置整理 |
| [002_GRILL_WITH_DOCS_RESULT.md](002_GRILL_WITH_DOCS_RESULT.md) | active | skill ecosystem / privateEval / docs 整理計画 |
| [003_GRILL_WITH_DOCS_RESULT.md](003_GRILL_WITH_DOCS_RESULT.md) | active | plugin update 失敗に対する safe repair fallback 導線 |
| [005_GRILL_WITH_DOCS_RESULT.md](005_GRILL_WITH_DOCS_RESULT.md) | active | skill 構造の簡素化と評価導線の分離 |
| [006_GRILL_WITH_DOCS_RESULT.md](006_GRILL_WITH_DOCS_RESULT.md) | active | skill 命名体系の全面刷新 |
| [007_GRILL_WITH_DOCS_RESULT.md](007_GRILL_WITH_DOCS_RESULT.md) | active | dotnet family を internal sub-skill 化する |
| [008_GRILL_WITH_DOCS_RESULT.md](008_GRILL_WITH_DOCS_RESULT.md) | superseded | GitHub-first knowledge storage と agent entrypoint。設計・実装の正本は [../design/008_TECHNICAL_DESIGN.md](../design/008_TECHNICAL_DESIGN.md) と [../plan/008_PLAN_DONE.md](../plan/008_PLAN_DONE.md) |
| [009_GRILL_WITH_DOCS_RESULT.md](009_GRILL_WITH_DOCS_RESULT.md) | superseded | repo-onboarding と guard の初回導線を穏やかにする。設計・実装の正本は [../design/009_TECHNICAL_DESIGN.md](../design/009_TECHNICAL_DESIGN.md) と [../plan/009_PLAN_DONE.md](../plan/009_PLAN_DONE.md) |

## 更新ルール

- 新しい grill result を追加したら、この一覧へ `active` として追加する。
- 後続の design / plan / ADR で置き換えた場合は、`superseded` に変更し、置き換え先を Topic に書く。
- 生ログではなく、Fact / Inference / Blocking Unknown / 次工程だけを残す。
