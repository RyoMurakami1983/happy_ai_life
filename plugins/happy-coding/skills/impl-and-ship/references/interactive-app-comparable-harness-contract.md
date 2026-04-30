# Interactive App Comparable Harness Contract

interactive app を **比較用 pilot** として進めるときに、stack 間の差分を比較可能にするための最小 contract です。

これは製品機能の仕様ではありません。目的は、言語差・UI 差・tooling 差を観測するときに、next queue や state dump 形式のぶれで比較が壊れないようにすることです。

以下の state や command は **Tetris pilot を例にした具体例** を含みます。別の interactive app では、同じ役割を持つ概念へ読み替えます。たとえば `next queue` や `hold state` は、将来状態や保持スロットのような同等概念がないアプリでは不要です。

## 1. Deterministic start

- deterministic seed を固定するか、同等の固定シナリオを用意する
- 目的は比較時の初期条件を揃えることであり、本番仕様から乱数を排除することではない
- 単一 stack の製品開発では必須ではないが、cross-stack 比較 pilot では原則推奨する

## 2. Common state dump schema

最低限、次を揃える:

- board または同等の可視状態
- active actor / active piece のような現在操作中の主体
- next queue や upcoming item のような将来状態
- hold state のような切替スロットや保持状態（該当する場合）
- score / level / lines
- last action または step counter

これらが揃うと、runtime evidence を screenshot だけに頼らず、state でも比較しやすくなります。

## 3. Common command runner

最低限、次の command 群を揃える:

- start
- pause
- left / right
- rotate または同等の主要変形操作
- soft-drop / hard-drop のような主要進行操作
- hold のような切替・保持操作（該当する場合）
- restart

command 名まで完全一致しなくてもよいですが、handoff / test / evaluator で同じ意味として辿れるようにします。

## 4. Scope boundary

- この contract は interactive app pilot の **comparable surface** を揃えるためのもの
- build / test / launch command の固定や `git init` 確認は bootstrap checklist の担当
- `PASS` / `FAIL` / `REPLAN_REQUIRED` の判定は `implementation-eval-gate` の担当
