# Implementation Eval Checklist

必要な観点だけを選んで使うための checklist です。PR 前の広い review ではなく、**1 slice の実装 gate** を想定しています。

## 1. 入力 artifact

- plan artifact または planning handoff を読んだか
- 今回の slice contract があり、done の定義と非対象が見えるか
- generator handoff と test / build / lint の証拠があるか

不足時の基本判定:

- 要件が曖昧 → `REPLAN_REQUIRED`
- 証拠が不足している → `FAIL` か `REPLAN_REQUIRED`

## 2. Requirement fit

- 差分は今回の slice contract に直接つながっているか
- 非対象を勝手に広げていないか
- 受け入れ条件のうち、何を満たしたか説明できるか

## 3. Behavioral correctness

- 期待された振る舞いが evidence 付きで確認できるか
- 失敗系や主要な境界値を見落としていないか
- 実装の見た目ではなく、ユーザー行動または契約された挙動で確認しているか

## 4. Regression risk

- 既存の主要フローを壊していないか
- 差分に対して確認すべき既存 test / smoke が実行されているか
- 一時しのぎの分岐や silent fallback で通していないか

## 5. Test adequacy

- failing test → 最小実装 → refactor の流れが追えるか
- 追加 test が 1 つの振る舞いに集中しているか
- 仕様上重要な分岐が test から漏れていないか

## 6. Security / trust boundary

- 認証、入力、機密、外部 I/O、コマンド実行を新たにまたいでいないか
- trust boundary 変更があれば、その確認結果が残っているか
- この観点で不安があれば `deep-review-preflight` や設計側への差し戻しが必要か

## 7. Verdict guide

### PASS

- slice contract を満たす
- 次の slice へ進める
- blocker が残っていない

### FAIL

- 計画や設計は概ね妥当
- ただし現 slice の実装に未達、欠陥、証拠不足がある
- generator が修正して戻るべき

### REPLAN_REQUIRED

- contract が曖昧
- plan / design と差分がずれている
- 現状の前提のまま直すより、順序・分割・構造判断を戻したほうが安全

## 8. 出力の原則

- verdict を先に書く
- failed criteria は具体的に書く
- evidence はファイル、テスト、ログ、または contract 条項に紐づける
- next action は `fix` / `replan` / `next-slice` のどれかに落とす
