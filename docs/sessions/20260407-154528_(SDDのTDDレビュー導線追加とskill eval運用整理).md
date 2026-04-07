# SDDのTDDレビュー導線追加とskill eval運用整理

## Executive Summary
- `/sdd` の flow を見直し、`planner` を計画の正本に保ったまま、実装前に `tdd-guide` のテスト戦略レビューを挟む形へ整理した。
- 変更後は `baseline / legacy / current` で比較 eval を実施し、session workspace 上の artifact から `current_vs_legacy` の改善を確認した。
- 続けて `/skill` を改善し、eval artifact は session workspace を既定、再利用価値のある `evals.json` と共有価値の高い `benchmark_summary/history` だけを repo の `evals/` へ昇格する方針を明文化した。

## Session Notes

### 主要な学び
- `tdd-guide` を計画の共同所有者にするより、`planner` の後でテスト戦略レビューを返す形のほうが責務境界と説明品質を両立しやすい。
- skill eval は session 側で materialize → aggregate → viewer まで回すと、試行錯誤の証跡を保ちつつ比較判断がしやすい。
- repo 側に残す artifact は少ないほど運用しやすく、`evals.json` と `benchmark_summary/history` に絞ると共有価値と repo の見通しを両立できる。

### 変更の要点
- `home-template/.copilot/skills/sdd/` の router と sub-skill を更新し、計画から実装へ移る前の TDD-ready checkpoint を追加した。
- session workspace 上で `/sdd` の eval suite と manual run を作り、`current_vs_legacy` の改善を benchmark で確認した。
- `home-template/.copilot/skills/skill/sub_skills/evaluate|improve` と `_eval/schemas/schemas.md` を更新し、session-local default と repo 昇格ルールを明文化した。

## Next Steps
- accepted な eval artifact を repo `evals/` へ昇格しやすくする helper や補助導線の自動化余地を点検する。
- 他の skill にも同じ session-local / promoted repo evals の方針が必要かを順次確認する。
