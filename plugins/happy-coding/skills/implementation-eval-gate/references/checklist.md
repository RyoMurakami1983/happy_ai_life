# Implementation Eval Checklist

1 slice の gate に使う checklist です。関係する項目だけ選びます。

## Input

- implementation handoff がある
- slice contract がある
- done 条件と非対象が見える
- public interface / test surface が見える
- RED / GREEN / acceptance command がある
- 差分を確認した

不足時の基本判定:

- contract が曖昧 → `REPLAN_REQUIRED`
- evidence が不足しているが contract は明確 → `FAIL`

## TDD Evidence

- RED を実際に見た
- RED の失敗理由が対象振る舞いと一致している
- GREEN を実際に見た
- REFACTOR 後も確認 command が通っている
- docs-only / config-only slice では、RED の代替 verification が明示されている

## Requirement Fit

- 差分は今回の slice contract に直接つながっている
- 非対象を勝手に広げていない
- 受け入れ条件のどれを満たしたか説明できる

## Behavioral Correctness

- public interface 経由で確認している
- private method や内部 collaborator の呼び出し回数を固定していない
- 失敗系や主要な境界値を見落としていない
- 一時しのぎの silent fallback で通していない

## Test Adequacy

- 追加 test が 1 つの振る舞いに集中している
- mock は system boundary に限られている
- 自分たちが制御する内部 module を過剰に mock していない
- test が実装詳細ではなく contract を守っている

## Interactive Runtime Evidence

- interactive app なら runtime launch command で起動している
- web なら初期描画、主要操作、必要時 screenshot/trace がある
- pygame / Python GUI なら loop 起動、入力イベント、state 変化がある
- desktop なら window 捕捉、主要 control、状態表示、restart 動線がある
- build/test だけで `PASS` にしていない

## Security / Trust Boundary

- 認証、認可、外部入力、機密、外部 I/O、コマンド実行を新たにまたいでいない
- trust boundary 変更がある場合、その確認結果が残っている
- 前提が崩れた場合は `REPLAN_REQUIRED` を検討している

## Verdict Guide

### PASS

- slice contract を満たす
- RED/GREEN/acceptance evidence がある
- blocker が残っていない

### FAIL

- 計画や設計は明確
- ただし現 slice の実装に未達、欠陥、証拠不足がある
- 同じ slice に戻れば前進できる

### REPLAN_REQUIRED

- contract が曖昧
- plan / design と差分がずれている
- 現状の前提のまま直すより、順序・分割・構造判断を戻したほうが安全

## Output

- verdict を先に書く
- failed criteria は具体的に書く
- evidence はファイル、テスト、ログ、または contract 条項に紐づける
- next action は `fix` / `replan` / `next-slice` のどれかに落とす
