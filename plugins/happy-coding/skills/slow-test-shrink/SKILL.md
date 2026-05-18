---
name: slow-test-shrink
description: >
  遅いテストを pure contract test と 最小限の boundary smoke test へ縮退する。Use when:
  subprocess / integration / hook / wrapper / matrix test が重く、focused checks だけで必要な安全確認を残したいとき。
license: Personal
---

# Slow Test Shrink

遅いテストをただ消すのではなく、守っていた契約を速いテストへ移してから縮退する workflow skill です。
ゴールは、回帰検出力を保ちながら、開発中と PR レビュー対応中の確認を focused checks で回せる状態にすることです。

成功条件は、削除した slow assertion が pure contract test、静的 compatibility test、または最小限の boundary smoke test のいずれかに対応していることです。
確認手段は、変更したテストと直接関連する実装契約だけに絞ります。ユーザーが明示しない限り、full pytest / full quality gate は実行しません。

## こんなときに使う

- subprocess や外部 CLI 起動を繰り返すテストが遅いとき
- integration test の組み合わせ爆発を pure contract test と代表 smoke test に分けたいとき
- wrapper / adapter / hook / shell script のテストを境界契約だけに縮退したいとき
- PR レビュー対応で、差分に直結する focused checks だけを回したいとき
- 速くしたいが、必要な安全確認を失いたくないとき

## 判断表

| 既存テストの役割 | 移し先 | 残す subprocess / integration |
| --- | --- | --- |
| 入力分類、正規化、allow / ask / deny の判断 | pure unit または contract test | 残さない |
| wrapper が engine へ stdin / env / cwd / args を渡す | 代表 smoke test | 1 本 |
| event ごとの response shape | pure response-shape test、必要なら smoke test | 多くても 1 本 |
| runtime 不在、temp file 失敗、timeout など wrapper 固有の fail-closed | 最小の wrapper contract test | 分岐ごとに 1 本 |
| OS / shell 互換性 | 静的 compatibility test + 代表 parity | 代表だけ |
| policy pattern の組み合わせ | pure parametrized unit test | 残さない |

## ワークフロー: 遅いテストを安全に縮退する

### Step 1 - ゴール、成功条件、確認手段を固定する

何を速くしたいか、どの検出力を失ってはいけないかを書き出します。focused checks で確認する前提をここで明示します。

なぜ: 確認範囲を差分と契約に絞ると、速さと回帰検出力を同時に守りやすくなります。

### Step 2 - 遅いテストが守っている契約を棚卸しする

1. subprocess なしで確認できる pure logic
2. wrapper / adapter の境界でしか確認できない契約
3. OS、shell、filesystem、network、external process の代表確認
4. 既に別テストで重複している契約

1 と 4 は削るか pure test へ移します。2 と 3 は代表 smoke test だけ残します。

### Step 3 - 削除前に速い契約テストを追加する

command deny pattern、path normalization、policy shape、優先順位などの判断は、engine や domain 関数を直接評価します。

### Step 4 - 境界 smoke test を最小化する

- wrapper が engine に接続できること
- stdin / env / cwd / args の代表受け渡し
- event ごとの response shape
- wrapper 固有の fail-closed 分岐
- OS 互換性を壊しやすい構文の静的確認

engine の判断を subprocess 越しに何十通りも回さないでください。

### Step 5 - focused checks だけ実行する

```powershell
uv run python -m pytest -q tests/test_target_contract.py tests/test_target_wrapper.py
uv run ruff check tests/test_target_contract.py tests/test_target_wrapper.py
uv run ty check tests/test_target_contract.py tests/test_target_wrapper.py
```

repo の tool が path 指定できない場合でも、ユーザーの明示承認なしに full gate へ広げません。

### Step 6 - レビュー用の削除対応表を残す

```markdown
| 削除した slow assertion | 新しい確認先 | 残した境界 smoke |
| --- | --- | --- |
| Bash 経由の rm variants | engine の pure parametrized test | wrapper 接続 1 本 |
| policy uniqueness fallback matrix | policy loader fallback unit test | なし |
| 実時間 timeout wait | 短縮 timeout の wrapper contract | timeout 分岐 1 本 |
```

## 注意点

- 削除だけで終わらせない。守っていた assertion を先に移す。
- engine の判断は pure test、wrapper の責務は接続と fail-closed に絞る。
- 実時間待ちを避け、fake runtime や短縮 timeout で確認する。
- ユーザーが明示しない限り、full pytest / full quality gate は実行しない。
- 外部 I/O、shell、OS 差分、hook 連携の代表確認を 0 にしない。

## 関連スキル

- `safe-refactor` - 振る舞いを変えずにテスト構造を整理するとき
- `debug` - 失敗の再現条件を証拠化してからテストへ落とすとき
- `deep-review-preflight` - PR 前に削った安全網の妥当性を確認するとき

## 出力形式

1. ゴール
2. 削除対象の slow tests
3. 残す契約
4. 移した pure tests
5. 残した境界 smoke tests
6. 実行した focused checks
7. 残リスク
