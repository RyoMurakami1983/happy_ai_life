# Interactive App Bootstrap Checklist

interactive app の pilot / downstream repo で、実装着手前に最低限そろっているべき前提を確認する checklist です。`/sdd` の bootstrap checkpoint で使い、足りない場合は実装を始める前に補います。

## 1. Target repo sync

- target repo に `.github/copilot-instructions.md` が存在するか
- target repo に `.github/instructions/` が存在するか
- 言語別 instructions が target repo の技術スタックと一致しているか
- 未配布なら `scripts/sync-to-repo.ps1 -TargetRepoPath PATH` 相当で配布するか、未配布のまま進める理由を handoff に明記したか

## 2. Common contract

- build / test / lint の入口が repo に存在するか
- generator handoff で test command と runtime launch command を返せる入口があるか
- interactive app の受け入れ条件に「live runtime で何を確認するか」が書かれているか

## 3. TypeScript / web

- fresh scaffold に test runner があるか（例: Vitest）
- dev / build / test の command が固定されているか
- runtime evaluator が起動できる URL または launch command があるか
- UI state を観測できる最低限の入口（title, control, canvas, screen text など）があるか

## 4. Python / pygame

- `python -m unittest discover ...` または採用した test command が安定して動く import 契約になっているか
- app の entrypoint と runtime launch command が 1 つに固定されているか
- pure logic と GUI loop が分かれ、state を test か runtime evaluator から追えるか
- runtime evaluator が画面状態または state dump を観測する手段があるか

## 5. WPF / desktop

- `dotnet build` の入口が固定されているか
- core logic を確かめる test project / test command が存在するか
- desktop app の launch command が 1 つに固定されているか
- FlaUI などで window title / control / status text / restart 動線を観測できる見込みがあるか

## 6. Fallback rule

- ここで不足が見つかったら、実装で埋めながら進めるのではなく bootstrap task として先に補う
- どうしても未整備のまま進める場合は、`implementation-eval-gate` に evidence gap として引き渡す
