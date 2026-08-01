# Loop Engineering 評価シナリオ

Loop Engineering が機能しているかを見るための代表シナリオです。
目的は満点を取ることではなく、**Observe から Stop or Loop まで進み、落ちた軸だけを Patch 対象にできるか**を確認することです。

## 共通の期待行動

- 事実、推測、未確認事項を分ける
- 成功条件と対象外を先に固定する
- 機械判定を PrivateEval より優先する
- PrivateEval 5軸で落ちた軸を明示する
- 差分を増やす前に Stop / Continue / Human Review を判断する

## 入口分類

| 入口 | 見ること | 代表的な完了 |
|---|---|---|
| bugfix loop | 再現、原因、最小修正、回帰確認 | 失敗が再現され、修正後の focused test が通る |
| review response loop | 指摘分類、必要修正、再確認、follow-up 化 | blocking 指摘が解消し、残件の行き先が分かる |
| authoring improvement loop | skill / prompt / docs の失敗ログ、評価軸、最小修正 | 変更理由と再評価方法が残り、必要なら eval case へ昇格する |

## Bugfix

### 入力例

既存テストが 1 件落ちている。エラーは `expected 10 but got 0`。関連コードは小さな集計関数で、最近の変更は条件分岐の追加だけ。

### Critical 要件

- [ ] エラーを再現する
- [ ] 原因と症状を分ける
- [ ] 最小差分で修正する
- [ ] 回帰確認を示す

## Feature Addition

### 入力例

既存 skill に「低リスク小タスクでは評価メモを軽量化してよい」ことを追加したい。

### Critical 要件

- [ ] 既存構造を読む
- [ ] trigger / body の責務を崩さない
- [ ] 利用者体験が変わるなら version 判断を行う
- [ ] 過剰なテンプレート追加にしない

## Authoring Improvement

### 入力例

既存 skill の説明と実際の導線がずれており、利用者が別 skill へ迷い込む。失敗ログと review 指摘が 2 件ある。

### Critical 要件

- [ ] 作成・責務整理は `copilot-authoring`、評価方法の選択は `skill-eval` と分ける
- [ ] 失敗ログから落ちた軸を 1 テーマに絞る
- [ ] 明瞭性が問題なら `empirical-prompt-tuning` へ渡す
- [ ] 再発確認できるなら `evals/<skill-id>/` への昇格候補を残す

## Debug Distillation

### 入力例

CLI の `update` が `Access is denied` で失敗した。証拠を集めると ACL や file lock ではなく、CLI の update / uninstall 経路だけが失敗していた。

### Critical 要件

- [ ] debug の証拠から Fact / Inference / Unknown を分ける
- [ ] 症状名だけで docs 化せず、誤診しやすい原因を潰す比較手順を残す
- [ ] 回避策は backup、対象 path、復旧確認を含める
- [ ] 汎用化しすぎず、今回の実セッションで確認した範囲に絞る

## Refactoring

### 入力例

同じチェックリストが 2 つの文書に重複している。片方を正本化し、もう片方は参照にしたい。

### Critical 要件

- [ ] 振る舞いや導線を変えない
- [ ] 正本と mirror / reference を分ける
- [ ] 参照切れを起こさない
- [ ] 無関係な文言変更を混ぜない

## Security Fix

### 入力例

サンプル設定に実在しそうな token 形式の値が含まれている。secret scan はまだ落ちていない。

### Critical 要件

- [ ] 秘密情報を残さない
- [ ] dummy 値へ置換する
- [ ] ログや説明に secret 形式を広げない
- [ ] 必要なら履歴上の扱いを Human Review に切り替える

## Performance

### 入力例

ある処理が遅いと言われたが、計測値がない。最適化案だけが先に提示されている。

### Critical 要件

- [ ] 推測で最適化しない
- [ ] 計測方法を先に決める
- [ ] 改善前後を比較する
- [ ] 過剰最適化を避ける

## 判定メモ

```markdown
Scenario:
- 種別:
- 成功 / 失敗:
- 落ちた軸:
- Continue する理由:
- Stop する理由:
- Human Review に切り替える理由:
```
