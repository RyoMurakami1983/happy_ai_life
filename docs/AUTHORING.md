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
- 基本導線は [Skill Map](SKILL_MAP.md) に接続する

## skill の最小構成

```text
plugins/<plugin>/skills/<skill-name>/SKILL.md
```

`SKILL.md` には次を入れます。

- 何をする skill か
- こんなときに使う
- 実行手順
- 成功条件

### skill 作成規律

`SKILL.md` は常時読まれる可能性があるため、入口、判断表、core loop、成功条件に絞ります。

| 規律 | 書くこと |
| --- | --- |
| leading word | skill 内で繰り返し使う短い概念を決め、意味をぶらさない |
| no-op pruning | モデルが既定でできる一般論や重複説明を削る |
| completion criterion | 「作業した」ではなく、何が確認できたら完了かを書く |
| progressive disclosure | 長い例、背景、書式は `references/` や `sub_skills/` へ逃がす |

詳細が長くなる場合は `SKILL.md` に詰め込まず、次のように分けます。

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/references/*.md
skills/<skill-name>/sub_skills/*/SKILL.md
```

### dependency / handoff

他 skill の後続として動く場合は、前提と handoff を明示します。

```markdown
## Handoff from design-and-plan

- implementation contract がある
- 成功条件が観測可能である
- 対象外が明記されている
```

中核導線は次を基本にします。

```text
grill-with-docs -> design-and-plan -> implement -> implementation-eval-gate
```

この導線に乗らない skill は、[Skill Map](SKILL_MAP.md) に接続先を追加するか、`works/` に留めます。

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
uv run python -m pytest -q tests/test_skill_map.py tests/test_evals_policy.py
uv run ruff check .
```

迷った場合は小さく作り、README の日常導線を増やしすぎないようにします。
