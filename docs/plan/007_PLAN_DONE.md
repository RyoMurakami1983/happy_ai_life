# PLAN 007

## GOAL

dotnet family を `dotnet` 配下の internal sub-skill へ再編し、公開入口を `dotnet` に一本化する。

## Success Criteria

- `dotnet` が thin family router になる
- dotnet family leaf が `sub_skills/*` に移る
- leaf 名が親文脈前提の短い名前になる
- docs / tests / validators が通る

## Out of Scope

- 他 family の再編
- 互換 shim
- plugin 名変更

## Progress

- [x] Bootstrap / 前提確認
- [x] Slice 1: Router contract rewrite
- [x] Slice 2: Sub-skill move
- [x] Slice 3: Docs / naming sync
- [x] Slice 4: Eval + review gate
- [x] Completion handoff

## Structure Decisions

- `dotnet` を唯一の公開入口にする
- family leaf は `dotnet/sub_skills/*` に置く
- `dotnet-` prefix は leaf では落とす
- `disable-model-invocation: true` を親に付ける

## Behavior List

- [x] `dotnet` が route / handoff だけを持つ
- [x] family leaf が top-level catalog から消える
- [x] `framework-bridge` / `setup` / `modern-cs` / `type-perf` / `cs-concurrency` / `wpf-*` / `slopwatch` / `nuget-local` が `dotnet` 配下に入る
- [x] docs と tests が新構造へ追随する

## Vertical Slices

### Slice 1: Router contract rewrite

- Type: AFK
- Done: `dotnet` 親が thin family router として再設計される
- First test: `uv run python -m pytest -q tests\\test_dotnet_router_docs.py`
- RED expectation: dotnet 親がまだ top-level leaf 前提のまま
- GREEN command: `uv run python -m pytest -q tests\\test_dotnet_router_docs.py`
- Acceptance command: `uv run python plugins\\happy-core\\skills\\copilot-authoring\\_skill\\_eval\\scripts\\validate_skill.py plugins\\happy-coding\\skills\\dotnet\\SKILL.md --level L2`
- Out of scope: 実移設

### Slice 2: Sub-skill move

- Type: AFK
- Done: dotnet family leaf が `sub_skills/*` に移る
- First test: `uv run python -m pytest -q tests\\test_skill_map.py tests\\test_plugin_manifest.py`
- RED expectation: top-level leaf 前提で mismatch
- GREEN command: `uv run python -m pytest -q tests\\test_skill_map.py tests\\test_plugin_manifest.py`
- Acceptance command: `uv run python -m pytest -q tests\\test_dotnet_router_docs.py tests\\test_skill_map.py tests\\test_plugin_manifest.py`
- Out of scope: 他 family

### Slice 3: Docs / naming sync

- Type: AFK
- Done: `docs/SKILL_MAP.md` と関連 docs が新構造を説明する
- First test: docs tests
- RED expectation: old slug / old path 残存
- GREEN command: `uv run python -m pytest -q tests\\test_dotnet_router_docs.py tests\\test_skill_map.py`
- Acceptance command: `uv run python -m pytest -q tests\\test_dotnet_router_docs.py tests\\test_skill_map.py tests\\test_plugin_manifest.py`
- Out of scope: empirical eval

### Slice 4: Eval + review gate

- Type: AFK
- Done: implementation gate / deep review / targeted checks 完了
- First test: integrated validation
- RED expectation: route / source of truth mismatch
- GREEN command: `uv run python -m pytest -q tests\\test_dotnet_router_docs.py tests\\test_skill_map.py tests\\test_plugin_manifest.py`
- Acceptance command: `uv run ruff check tests\\test_dotnet_router_docs.py`
- Out of scope: PR 作成

## Order Rationale

- 先に親の contract を fix してから leaf を移した方が、受け皿と naming がぶれない。
- その後に物理移設と docs/test 更新をまとめてやる。

## Risks / Unknowns

- `nuget-local` を family に含めることへの違和感が後から出る可能性
- sub_skills 構造で discoverability が足りるかは docs と router quality に依存する

## Return Conditions

- FAIL: route や rename の漏れが局所修正で直る
- REPLAN_REQUIRED: family 全部移設より、一部 top-level 維持が必要と判明する
