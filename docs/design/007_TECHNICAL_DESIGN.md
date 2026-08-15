# Technical Design 007: dotnet family router への再編

## Goal

`dotnet` を唯一の公開入口にし、dotnet 関連 skill を internal sub-skill へ再編する。公開一覧を短く保ちつつ、family 内の leaf は親文脈つきの短い名前へ寄せる。

## Success Criteria

- `plugins/happy-coding/skills/dotnet/SKILL.md` が family router として再設計される。
- dotnet family の leaf skill が `dotnet/sub_skills/*` に移設される。
- top-level の dotnet leaf は公開 skill 一覧から外れる。
- skill map / plugin manifest test / naming docs が新構造を前提に通る。
- deep review と implementation gate で `PASS` 相当の evidence が残る。

## Out of Scope

- ts / linux など他 family の同時再編
- 旧 dotnet leaf slug の shim 追加
- plugin 名変更

## Context / Source of Truth

- `CONTEXT.md`
- `docs/AUTHORING.md`
- `docs/SKILL_MAP.md`
- `plugins/happy-coding/skills/dotnet/SKILL.md`
- `tests/test_skill_map.py`
- `tests/test_plugin_manifest.py`

## Structure Decisions

### 1. Public surface

公開入口は `dotnet` のみとする。family 内の専門 skill は slash / catalog の top-level 列挙から外し、`dotnet` の内部 route として持つ。

### 2. Directory shape

```text
plugins/happy-coding/skills/dotnet/
  SKILL.md
  sub_skills/
    framework-bridge/
    setup/
    modern-cs/
    type-perf/
    cs-concurrency/
    wpf-mvvm/
    wpf-secure-config/
    slopwatch/
    nuget-local/
```

`dotnet` 配下の leaf は親文脈が補うため、`dotnet-` prefix を落とす。

### 3. Naming

| 現在 | dotnet 配下での名前 |
| --- | --- |
| `dotnet-framework-netstandard-bridge` | `framework-bridge` |
| `dotnet-setup-dev-environment` | `setup` |
| `dotnet-modern-cs` | `modern-cs` |
| `dotnet-type-perf` | `type-perf` |
| `dotnet-cs-concurrency` | `cs-concurrency` |
| `dotnet-wpf-mvvm-patterns` | `wpf-mvvm` |
| `dotnet-wpf-secure-config` | `wpf-secure-config` |
| `dotnet-slopwatch` | `slopwatch` |
| `nuget-local` | `nuget-local` |

### 4. Router behavior

`dotnet` 親は `disable-model-invocation: true` を持つ thin orchestration に寄せる。役割の境界、実行ルール、迷ったときの判断だけを置き、詳細実装は各 child skill に移す。

### 5. Compatibility

旧 top-level slug からの直接 invocation は breaking change として扱う。PR 本文と docs に移行注意を書く。

## Public Interfaces / Test Surface

- `plugins/happy-coding/skills/dotnet/SKILL.md`
- `plugins/happy-coding/skills/dotnet/sub_skills/*/SKILL.md`
- `docs/SKILL_MAP.md`
- `tests/test_skill_map.py`
- 命名 / route consistency の新規 test

## Behavior List

- [ ] `dotnet` が family router として internal route を説明する
- [ ] family leaf が top-level 一覧から消える
- [ ] family leaf の名前が親文脈前提の短縮名になる
- [ ] docs と tests が新構造を正本とする
- [ ] compatibility caveat を残す

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| 1. Router contract rewrite | AFK | `dotnet` 親が thin router として書き換わる | new docs test | 旧 top-level 前提のまま | targeted pytest |
| 2. Sub-skill move | AFK | dotnet leaf が `sub_skills/` に移る | skill map / plugin tests | missing dir / old refs | targeted pytest |
| 3. Docs / naming sync | AFK | skill map, ask-happy 相当 docs が追随 | docs tests | old slug remains | targeted pytest |
| 4. Eval + review gate | AFK | implementation gate / deep review / validators 完了 | integrated checks | route inconsistency | integrated checks |

## Risks / Unknowns

- plugin loader が `sub_skills/` を独立公開 skill として扱わない前提は repo test で固定されているが、実ランタイムでの discoverability も確認した方がよい。
- `nuget-local` を dotnet family に含めるかは文脈的には自然だが、利用者が独立 skill として覚えている可能性はある。

## ADR

- 既存の naming / orchestration ADR に追補する。新規 ADR は不要。

## Implementation Handoff

### Goal

dotnet family を top-level の flat list から、`dotnet` 配下の internal sub-skill 構造へ移す。

### Success Criteria

- `dotnet` が唯一の公開入口になる。
- leaf が `sub_skills/*` に移り、短い名前になる。
- docs / tests / plugin validation が通る。

### Out of Scope

- 他 family の再編
- 互換 shim

### Artifacts

artifacts:
  - docs/grill_results/007_GRILL_WITH_DOCS_RESULT.md
  - docs/design/007_TECHNICAL_DESIGN.md
  - docs/plan/007_PLAN_DONE.md

### Commands

```powershell
uv run python -m pytest -q tests/test_skill_map.py tests/test_plugin_manifest.py tests/test_dotnet_router_docs.py
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-coding\skills\dotnet\SKILL.md --level L2
uv run ruff check tests\test_dotnet_router_docs.py
```

### Return Conditions

- FAIL: 移設後の参照漏れが局所修正で直る
- REPLAN_REQUIRED: internal sub-skill 構造だと実ランタイム上で必要な discoverability を満たせない
