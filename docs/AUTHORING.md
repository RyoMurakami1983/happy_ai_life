# 作成ガイド

この repo は Copilot CLI 向けの skill、agent、repository instructions を扱います。

## 使い分け

| 種類 | 使う場面 |
|---|---|
| skill | 手順や判断基準を再利用したい |
| agent | 特定の役割で独立して調査・実装させたい |
| instructions | repo 全体または path ごとの常時ルールを置きたい |

## 最小方針

- まず既存例を探す
- 1つの目的に絞る
- trigger は短く具体的に書く
- secret、hook bypass、破壊的操作を許可しない
- 作ったら focused test または手動確認を残す

## skill の最小構成

```text
plugins/<plugin>/skills/<skill-name>/SKILL.md
```

`SKILL.md` には次を入れます。

- 何をする skill か
- こんなときに使う
- 実行手順
- 成功条件

## agent の最小構成

```text
plugins/<plugin>/agents/<agent-name>.md
```

agent には役割、入力、完了条件、使ってよい tool の範囲を書きます。

## instructions

repo-wide instructions は `.github/copilot-instructions.md` に置きます。path 固有の補足は `.github/instructions/` に置きます。

## 確認

```powershell
uv run python -m pytest -q tests/test_repo_local_skill_policy.py
uv run ruff check .
```

迷った場合は小さく作り、README の日常導線を増やしすぎないようにします。
