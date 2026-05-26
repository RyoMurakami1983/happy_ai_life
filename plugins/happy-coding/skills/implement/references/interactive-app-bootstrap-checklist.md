# Interactive App Bootstrap Checklist

この checklist は **母艦 repo 側の正本** です。interactive app の pilot / downstream repo では、sync 済みのコピーを読みながら、実装着手前に最低限そろっているべき前提を確認します。`implement` の bootstrap checkpoint（ステップ 2）で使い、足りない場合は実装を始める前に補います。

## 1. Target repo sync

- `repo-template` / `scripts/sync-to-repo.ps1` は母艦 repo の source of truth であり、downstream repo では配布済みの結果を前提に読む

- target repo に `.github/copilot-instructions.md` が存在するか
- target repo に `.github/instructions/` が存在するか
- 言語別 instructions が target repo の技術スタックと一致しているか
- 未配布なら `scripts/sync-to-repo.ps1 -TargetRepoPath PATH` 相当で配布するか、未配布のまま進める理由を handoff に明記したか
- target repo が `git init` 済みで `.git/` を持つか
- `.githooks/` や `core.hooksPath` の確認が必要な flow なら、Git 初期化前に「bootstrap 完了」と見なしていないか

## 2. Common contract

- build / test / lint / launch の入口が repo に存在するか
- generator handoff で test command と runtime launch command を返せる入口があるか
- interactive app の受け入れ条件に「live runtime で何を確認するか」が書かれているか
- どの stack でも 1 つに固定した build / test / launch command を返せるか
- interactive app の比較 pilot なら、minimum comparable harness contract を採用するか判断したか
  - deterministic seed または同等の固定シナリオ
  - 共通 state dump schema
  - 共通 command runner
- これらが未整備なら bootstrap task として先に補うか、未整備の理由を handoff / eval に明記したか

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
- bootstrap 完了は少なくとも次の 3 点を満たす
  - target repo への template / instructions 配布
  - `git init` 済み
  - build / test / launch command の固定

## 7. Comparable harness contract for pilot

この節は **比較用 pilot** のときに使います。通常の製品開発で seed 固定を必須にする意図ではありません。

- 詳細な正本は `references/interactive-app-comparable-harness-contract.md`

- deterministic seed を固定するか、同等の固定シナリオを用意するか
  - 目的は next queue や初期状態の差で比較がぶれないようにすること
  - 乱数自体を本番仕様から取り除くことが目的ではない
- state dump の最低項目を揃えるか
  - board または同等の可視状態
  - active piece
  - next queue
  - hold state
  - score / level / lines
  - last action または step counter
- command runner の最低 command を揃えるか
  - start
  - pause
  - left / right
  - rotate
  - soft-drop / hard-drop
  - hold
  - restart
