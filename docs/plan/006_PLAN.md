# PLAN 006

## GOAL

skill 命名を、誤解しにくさ優先・短さ従属の原則で刷新し、context-unique な child / leaf だけを短縮する。

## Success Criteria

- 命名ポリシーが docs / conventions / ADR に残る。
- `disable-model-invocation` が intent-only として明記される。
- 第一弾 rename が実ディレクトリ、frontmatter、docs、tests で一致する。
- targeted validation が通る。

## Out of Scope

- plugin 名変更
- 全 skill 一括 rename
- slash command 可視性制御

## Progress

- [x] Bootstrap / 前提確認
- [ ] Slice 1: 命名ポリシー文書化
- [ ] Slice 2: authoring child rename
- [ ] Slice 3: setup / dotnet leaf rename
- [ ] Slice 4: Integration validation
- [ ] Completion handoff

## Structure Decisions

- plugin 名は維持する。
- top-level / evaluation / safety / entrypoint skill は説明的に保つ。
- child / leaf のみ、文脈一意なら略称を許す。
- `ts`, `py`, `cs`, `perf` は候補、`eval` は避ける。

## Behavior List

- [ ] `disable-model-invocation` の扱いが docs で一貫する
- [ ] `instructions-authoring` / `improve-existing` / `validate-authoring` が rename される
- [ ] `ts-setup` / `py-setup` / `ts-tauri` など第一弾 rename が反映される
- [ ] dotnet leaf の一部が短縮される
- [ ] skill map / tests が新名を正本とする

## Vertical Slices

### Slice 1: 命名ポリシー文書化

- Type: AFK
- Done: 命名規約と `disable-model-invocation` 運用が docs / conventions / ADR に入る
- First test: `uv run python -m pytest -q tests\test_skill_naming_docs.py`
- RED expectation: test が未作成または新ルール未記載で失敗する
- GREEN command: `uv run python -m pytest -q tests\test_skill_naming_docs.py`
- Acceptance command: `uv run ruff check tests\test_skill_naming_docs.py`
- Out of scope: 実 rename

### Slice 2: authoring child rename

- Type: AFK
- Done: `instructions` / `improve` / `validate` へ rename され、docs / tests が追随する
- First test: `uv run python -m pytest -q tests\test_copilot_authoring_docs.py tests\test_skill_map.py`
- RED expectation: 旧 slug のままで mismatch
- GREEN command: `uv run python -m pytest -q tests\test_copilot_authoring_docs.py tests\test_skill_map.py`
- Acceptance command: `uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\copilot-authoring\SKILL.md --level L2`
- Out of scope: setup / dotnet leaf

### Slice 3: setup / dotnet leaf rename

- Type: AFK
- Done: 第一弾 leaf rename が反映される
- First test: `uv run python -m pytest -q tests\test_skill_map.py tests\test_plugin_manifest.py`
- RED expectation: 旧 slug 参照や missing dir で失敗する
- GREEN command: `uv run python -m pytest -q tests\test_skill_map.py tests\test_plugin_manifest.py`
- Acceptance command: `uv run python -m pytest -q tests\test_skill_naming_docs.py tests\test_skill_map.py tests\test_plugin_manifest.py`
- Out of scope: 残り全 skill の rename

### Slice 4: Integration validation

- Type: AFK
- Done: targeted tests / validators / ruff が通る
- First test: integrated validation
- RED expectation: references や docs の rename 漏れ
- GREEN command: `uv run python -m pytest -q tests\test_skill_naming_docs.py tests\test_copilot_authoring_docs.py tests\test_skill_map.py tests\test_plugin_manifest.py`
- Acceptance command: `uv run ruff check tests\test_skill_naming_docs.py tests\test_copilot_authoring_docs.py`
- Out of scope: full suite

## Order Rationale

- 先に naming rule を決めないと rename 判定がぶれる。
- 次に親文脈が強い authoring child を rename し、パターンを安全に固定する。
- その後、第一弾 leaf rename をまとめて適用する。

## Risks / Unknowns

- dotnet leaf のどこまでを短縮しても推測可能かは、実名を見ながら調整が必要。
- 既存 docs で旧 slug を説明として残した方がよい箇所があるかもしれない。

## Return Conditions

- FAIL: rename 漏れが局所修正で直る
- REPLAN_REQUIRED: alias 互換層が必要と分かった場合
