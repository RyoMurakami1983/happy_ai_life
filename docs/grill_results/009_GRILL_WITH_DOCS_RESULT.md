# 009 GRILL WITH DOCS RESULT: repo-onboarding と guard の初回導線を穏やかにする

## 対象の目的

repo-onboarding 時の guard friction を減らし、未知 repo の初回導入では **Read-only 観測 -> BootstrapMinimal で bootstrap -> 必要なら HappyDefault へ昇格** の順で進めやすくする。

## 重要な判断軸

- **安全性**: 破壊的操作や guard bypass は引き続き防ぐ
- **低摩擦**: onboarding の観測や初回 bootstrap で不要に止めない
- **責務分離**: home-level guard、repo-local policy、repo-onboarding skill の責務を混ぜない
- **再現性**: bootstrap 状態を script と check で同じように評価できる
- **拡張性**: downstream repo が後で HappyDefault へ昇格できる

## 役割と責任

- `home-template/.copilot/`: user-global bootstrap と safety valve の配布
- `policy/guard-policy*.json`: guard policy の profile 定義
- `sync-to-home*`: home へ managed policy surface を同期
- `sync-to-repo*`: downstream repo へ `.github/`, `.githooks`, `policy/` を同期
- `repo-secure-check*`: bootstrap 状態を blocking / advisory 付きで評価
- `repo-onboarding`: Read-only / Bootstrap の進行型

## 例外・異常系

- repo 未整備で `repo-secure-check` が advisory を返しても、blocking がなければ onboarding を続行できる
- home-level maintenance mode や destructive command deny は BootstrapMinimal でも緩めない
- policy ファイルが読めなくても fallback は fail-open にしない

## 成功条件

- `BootstrapMinimal` profile が `sync-to-repo` で選べる
- `repo-secure-check` の JSON と表示に severity が入る
- `repo-onboarding` が BootstrapMinimal -> HappyDefault 昇格の考え方を説明する
- home sync で bootstrap policy も配布される
- focused test が新しい profile と severity を固定する

## 失敗条件

- onboarding を軽くした結果、破壊的 deny や maintenance mode deny が緩む
- BootstrapMinimal と HappyDefault の差が docs / scripts / tests でずれる
- `repo-secure-check` が severity 追加後に既存利用を壊す

## 事実 / 解釈 / 未確認

### 事実

- `repo-onboarding` はすでに Read-only / Bootstrap mode を持つ
- `repo-secure-check` は現在 `ok` だけで severity を持たない
- `sync-to-repo` の policy profile は `HappyDefault / Secure / EnterpriseStrict / WindowsDesktop` のみ
- guard evaluator は observe tool を fileWrite と分けている

### 解釈

- friction の主因は protected path の read そのものより、bootstrap 時に full profile を前提にした all-or-nothing check と profile 選択肢の不足にある
- まずは `BootstrapMinimal` と severity 追加が最も効果が高い

### 未確認

- 将来 `allowObserve` を policy schema に入れるべきか
- downstream repo 向け専用 onboarding skill を別 file として切るか、既存 `repo-onboarding` を育てるか

## 次工程への引き継ぎ

- [design: 009_TECHNICAL_DESIGN.md](../design/009_TECHNICAL_DESIGN.md)
- [plan: 009_PLAN_DONE.md](../plan/009_PLAN_DONE.md)
- [grill index](README.md)
