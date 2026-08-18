# BootstrapMinimal と severity-aware repo-secure-check を採用する

**ステータス**: 承認

## 背景

`repo-onboarding` は既存 repo を短時間で理解し、必要なら bootstrap 完了まで進める skill である。  
しかし初回導入時から `HappyDefault` 相当の repo-local protected-path prompt と all-or-nothing な `repo-secure-check` を前提にすると、
onboarding の観測や bootstrap 完了判定が重くなりやすい。

調査の結果、初回導入では **破壊的 deny を維持しつつ、repo-local protected-path prompt は後段へ回す** 方が、
開発を止めずに安全性を保ちやすいと判断した。

## 判断

- 初回 bootstrap 用に `BootstrapMinimal` policy profile を導入する
- `BootstrapMinimal` は destructive deny command rules と safety-hook / guard-policy 自体の保護を維持し、より広い repo-local protected path の `ask` を後段へ回す
- bootstrap 後の steady-state は `HappyDefault` を既定とする
- `repo-secure-check` は各項目に `severity` を持ち、少なくとも `blocking` / `advisory` を区別する
- bootstrap 完了条件は「blocking 項目がすべて `OK`」とする
- policy file が欠けた / 壊れた場合の guard fallback は fail-closed を優先し、BootstrapMinimal より強い baseline に戻ってよい

## 根拠

- GitHub / Microsoft / VS Code の public pattern は、薄い onboarding 導線と局所 hard guard を組み合わせる傾向にある
- 初回導入では観測や scaffold 同期を優先し、強い repo-local protected-path prompt を最初から持ち込まない方が friction が少ない
- `repo-secure-check` の結果を severity 付きで返すと、advisory を follow-up に回しやすくなる

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| 常に HappyDefault | steady-state の一貫性が高い | 初回導入の摩擦が高い |
| **BootstrapMinimal -> HappyDefault** | 初回導入を軽くしつつ、定常運用で guard を戻せる | profile 昇格の 1 手間が増える |
| 常に BootstrapMinimal | friction は低い | steady-state の protected-path prompt が弱くなる |

## 運用

- `sync-to-repo` は `-PolicyProfile BootstrapMinimal` を受け付ける
- 初回導入では BootstrapMinimal を使い、`repo-secure-check` の blocking 項目をそろえる
- その後 `sync-to-repo -PolicyProfile HappyDefault` で昇格する
- `repo-onboarding` はこの二段階を標準導線として説明する
- `repo-secure-check -Strict` は互換維持のため全項目 green を基準とし、Bootstrap onboarding の完了判定は `-AsJson` の severity を使う
