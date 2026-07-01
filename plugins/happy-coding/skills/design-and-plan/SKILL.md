---
name: design-and-plan
description: >
  要求や仕様から、実装に渡せる構造判断、vertical slices、HITL/AFK 区分、behavior list、plan artifact を作る入口。
  Use when: grill-with-docs 後に設計判断と実装計画を作りたいとき、既存 repo の変更を TDD 可能な slice に分けたいとき、multi-repo や境界設計が必要か判断したいとき。
---

# design-and-plan — 設計を実装契約に変える

要求や仕様を、`implement` がそのまま TDD で進められる契約に落とします。
この skill は router です。標準設計で足りる場合は軽く進め、multi-repo や境界リスクがある場合だけ Balanced Coupling へ切り替えます。

## こんなときに使う

- grill 後の要求を実装可能な構造判断へ落としたいとき
- 既存 repo の変更を TDD 可能な vertical slice に分けたいとき
- HITL / AFK の切り分けを実装前に決めたいとき
- multi-repo や所有境界の設計が必要か判断したいとき
- `implement` へ渡す handoff を作りたいとき

## Core Loop

```text
grill result / spec
  -> goal and success criteria
  -> route selection
  -> structure decisions
  -> behavior list
  -> vertical slices
  -> implementation handoff
```

## 判断表

| 状況 | ルート | 判断 |
|---|---|---|
| 単一 repo、既存 stack、通常の機能追加 | `sub_skills/standard/` | 既定ルート |
| 新規 product / stack 未確定 / 大きな採用判断 | `sub_skills/standard/` + 技術選定 checkpoint | MVP 技術選定を明示する |
| 複数 repo、shared library、SDK、microservice、別チーム所有 | `sub_skills/balanced-coupling-design/` | provide / require と統合距離を見る |
| 境界が崩れている、分散モノリス化、過剰共有が疑われる | `sub_skills/balanced-coupling-design/` | 結合の 3 次元で評価する |

迷ったら `standard` から始めます。境界設計が実際に問題になった時点で Balanced Coupling へ切り替えます。

## 共通の設計 lens

どのルートでも、次を短く確認します。

- **Goal**: 何が成立したら終わりか
- **Success criteria**: 観測可能な完了条件
- **Structure**: どこに責務を置き、どこを触らないか
- **Interface as test surface**: どの public interface で確認するか
- **Vertical slices**: 1 ユーザー行動または 1 acceptance condition ごとに切る
- **HITL / AFK**: 人間判断が必要な slice と自走できる slice を分ける
- **Deletion pressure**: 追加する抽象化が、消す・置き換える・狭める余地を残しているか
- **Security boundary**: 外部入力、認証/認可、機密情報、コマンド実行、ファイル I/O の境界

## 出力

最終的に `implement` へ渡せる implementation handoff を作ります。

handoff に含めるもの:

- ゴール
- 成功条件
- 対象外
- 構造判断
- public interface と behavior list
- vertical slices（HITL / AFK を明示）
- 各 slice の最初の test 観点
- `artifacts:` フィールド（`artifacts: conversation-only` または保存した path の列挙）
- 実行 command
- 未決定事項と戻り先

設計書が必要な場合、またはユーザーが設計書の保存を明示した場合は `docs/design/NNN_TECHNICAL_DESIGN.md` に保存します。
実装進行用の checklist が必要な場合、またはユーザーが計画書の保存を明示した場合は `docs/plan/NNN_PLAN.md` を作ります。
成果物の path、命名、番号共有は `references/WORK_ARTIFACTS.md` に従います。

## 注意点

- router に詳細プロセスを書き込まない。詳細は sub-skill に置く。
- MVP 技術選定を毎回通さない。既存 stack で自然に進められるなら省略する。
- Balanced Coupling を毎回通さない。multi-repo、所有境界、統合リスクがあるときだけ使う。
- 実装をここで始めない。handoff を作ったら `implement` へ渡す。
- 仕様の穴を設計で埋めない。blocking unknown があれば `grill-with-docs` に戻す。

## 共通リソース

- `_foundation/DDD_GLOSSARY.md` — DDD と Balanced Coupling モデルの用語集
- `_foundation/IMPLEMENTATION_HEURISTICS.md` — サブドメイン分類から実装パターンを導く判断ツリー
- `_foundation/TECH_SELECTION_HARNESS.md` — 技術選定が必要な場合だけ読む
- `references/WORK_ARTIFACTS.md` — 成果物規約
- `assets/NNN_PLAN_TEMPLATE.md` — PLAN テンプレート
- `sub_skills/standard/` — 既定ルート
- `sub_skills/balanced-coupling-design/` — multi-repo / 境界設計ルート
