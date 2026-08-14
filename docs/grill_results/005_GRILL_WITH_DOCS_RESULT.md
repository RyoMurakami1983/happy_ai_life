# 005 PRD: skill 構造の簡素化と評価導線の分離

## Goal

Happy AI Life の skill 構造を、利用者から見て迷いにくく、保守者から見て責務を追いやすい形へ整理する。特に `copilot-authoring` は薄い入口に保ち、`new-agent` を公開導線から外し、authoring と evaluation の境界を明確にする。

## Fact

- `copilot-authoring` は authoring の薄い親として残す方針で合意した。
- `new-agent` は通常導線では作らないため、公開 child route から外す方針で合意した。
- `instructions-authoring` は常駐 instructions の authoring であり、skill authoring とは runtime semantics が異なるため独立維持する。
- `validate-authoring` は静的・構造確認であり、authoring 親の下に残す。
- `privateEval` は「secret を含まない評価ケースの設計・保管・昇格判断」を担う層として定義した。
- `skill-eval` は evaluation の公開入口、`empirical-prompt-tuning` は明瞭性の反復改善として独立維持する。
- `loop-engineering` は調査・修正・検証・評価・反映をまたぐ改善ループであり、evaluation 資産そのものは所有しない。

## Inference

- authoring と evaluation を 1 つの skill に戻すと、作成・改善・検証・評価の責務が再び混ざる。
- `private-eval` をトップレベル skill にすると発見性は上がるが、公開入口が増えすぎる。
- `private-eval` を `skill-eval` の reference / 内部ルートとして扱えば、責務は分けつつ slash command surface を増やさずに済む。
- `new-agent` は reference 化または issue 化で十分であり、公開 route として維持する必要は薄い。

## Success Criteria

- `copilot-authoring` の公開 route から `new-agent` が消えている。
- `new-skill` は agent 作成を通常導線にせず、必要時は例外扱いにする。
- `skill-eval` が evaluation 親として、`privateEval` / benchmark / empirical / loop-engineering の境界を説明している。
- `privateEval` の定義が `CONTEXT.md`、`docs/PRIVATE_EVAL.md`、`skill-eval` 周辺で矛盾しない。
- skill map / authoring docs / ADR / tests が新構造を説明している。

## Out of Scope

- Copilot CLI の slash command 表示制御を実装すること。
- 新しい `private-eval` top-level skill を作ること。
- 新しい custom agent を作ること。
- 実際の benchmark campaign を走らせること。

## Next

`docs/design/005_TECHNICAL_DESIGN.md` と `docs/plan/005_PLAN.md` に落とし、vertical slice ごとに実装・検証・commit する。
