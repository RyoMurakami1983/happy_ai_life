# Technical Design 006: skill 命名体系の全面刷新

## Goal

skill 名を全面的に見直し、初見利用者が役割を推測できることを守りながら、長すぎる slug を段階的に短くする。あわせて `disable-model-invocation` を visibility control ではなく orchestration intent として位置づける。

## Success Criteria

- 命名ポリシーが repo の authoring source of truth に追加される。
- rename 対象が「保護対象」と「短縮許可対象」に分類される。
- 文脈で一意な child / leaf slug の第一弾 rename が反映される。
- docs / tests / skill map / references が新命名で一貫する。

## Out of Scope

- plugin 名の変更。
- top-level / evaluation / safety / entrypoint skill の大規模 rename。
- slash command の表示名制御。

## Context / Source of Truth

- `CONTEXT.md`
- `docs/AUTHORING.md`
- `docs/SKILL_MAP.md`
- `plugins/happy-core/skills/copilot-authoring/_skill/_foundation/CONVENTIONS.md`
- `plugins/happy-coding/skills/interview-with-docs/SKILL.md`
- `plugins/happy-core/skills/ask-happy/SKILL.md`

## Structure Decisions

### 1. 命名ポリシー

- **保護対象**: plugin 名、top-level skill、evaluation / safety / entrypoint skill
- **短縮許可対象**: 親文脈で一意になる child / leaf skill
- **略称ルール**: `ts`, `py`, `cs` のような一般的 developer 略称は可。`eval`, `author`, `plan` のように広義で衝突しやすい語は避ける。

### 2. 第一弾 rename の対象

初見ユーザーが推測しやすく、かつ長すぎる slug から着手する。

| 現在 | 変更後 | 理由 |
| --- | --- | --- |
| `instructions-authoring` | `instructions` | `copilot-authoring` 配下では一意 |
| `improve-existing` | `improve` | 親文脈で一意、意味が残る |
| `validate-authoring` | `validate` | 親文脈で一意、実行意図が明確 |
| `typescript-setup-dev-environment` | `ts-setup` | 一般的略称、目的が保たれる |
| `python-setup-dev-environment` | `py-setup` | 一般的略称、目的が保たれる |
| `typescript-tauri-setup` | `ts-tauri` | `typescript` を `ts` に短縮しつつ文脈を保持 |
| `dotnet-csharp-concurrency-patterns` | `dotnet-cs-concurrency` | `dotnet` を維持しつつ `csharp` を短縮 |
| `dotnet-modern-csharp-coding-standards` | `dotnet-modern-cs` | 冗長語を整理して役割を残す |
| `dotnet-type-design-performance` | `dotnet-type-perf` | `performance` を文脈一意な短縮へ |

### 3. `disable-model-invocation`

`disable-model-invocation: true` は orchestration 親が route / handoff に徹する意図を示す。Copilot CLI では manual-only や slash 非表示を保証する機能とはみなさない。

## Public Interfaces / Test Surface

- `plugins/*/skills/**/SKILL.md` frontmatter `name`
- directory slug
- `docs/SKILL_MAP.md`
- `docs/AUTHORING.md`
- `plugins/happy-core/skills/copilot-authoring/_skill/_foundation/CONVENTIONS.md`
- 命名ポリシーの docs test
- `tests/test_skill_map.py`
- `tests/test_plugin_manifest.py`

## Behavior List

- [ ] 命名ポリシーが docs / conventions / ADR に残る
- [ ] `disable-model-invocation` が intent-only として説明される
- [ ] `instructions-authoring` / `improve-existing` / `validate-authoring` が短縮名へ変わる
- [ ] `ts` / `py` / `dotnet-*` の第一弾 rename が docs と tests に反映される
- [ ] 初見読者が新名を見て用途を推測できる

## Vertical Slices

| Slice | HITL/AFK | Done | First Test | RED Expectation | Commands |
|---|---|---|---|---|---|
| 1. 命名ポリシー文書化 | AFK | naming rules と `disable-model-invocation` の扱いが docs に入る | docs test | ルール未記載 | targeted pytest |
| 2. authoring child rename | AFK | `instructions` / `improve` / `validate` に rename され docs が追随 | skill map / docs test | 旧 slug 参照が残る | targeted pytest |
| 3. setup / dotnet leaf rename | AFK | `ts-*` / `py-*` / `dotnet-*` 第一弾 rename が追随 | skill map / plugin manifest / references | 旧 slug mismatch | targeted pytest |
| 4. integration | AFK | validator / ruff / manifest / skill map が通る | integrated checks | 不整合 | integrated checks |

## Risks / Unknowns

- rename 数が多いため、docs や references の取りこぼしが起きやすい。
- global skill list では parent 文脈が欠けるため、略称が短すぎると逆に不明瞭になる。
- `disable-model-invocation` の Copilot CLI 挙動は将来変わりうる。規約では意図と運用を分けて書く。

## ADR

- 新しい ADR は不要。既存の `skill-single-responsibility-and-orchestration` を拡張し、命名と `disable-model-invocation` の運用を追記する。

## Implementation Handoff

### Goal

誤解しにくさ優先の命名ポリシーを作り、child / leaf の第一弾 rename を repo 全体へ反映する。

### Success Criteria

- naming policy が docs / conventions / ADR にある。
- 第一弾 rename が実ディレクトリ、frontmatter、docs、tests で一致する。
- `disable-model-invocation` の扱いが明文化される。

### Out of Scope

- plugin 名変更。
- 全 skill 一括 rename。

### Artifacts

artifacts:
  - docs/grill_results/006_GRILL_WITH_DOCS_RESULT.md
  - docs/design/006_TECHNICAL_DESIGN.md
  - docs/plan/006_PLAN.md

### Commands

```powershell
uv run python -m pytest -q tests/test_skill_map.py tests/test_plugin_manifest.py tests/test_skill_naming_docs.py
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\happy-core\skills\copilot-authoring\SKILL.md --level L2
uv run ruff check tests\test_skill_naming_docs.py
```

### Return Conditions

- FAIL: 旧 slug 参照や rename 漏れが局所修正で直る
- REPLAN_REQUIRED: rename 数が多すぎて一括反映より alias / 段階移行が必要と判明する
