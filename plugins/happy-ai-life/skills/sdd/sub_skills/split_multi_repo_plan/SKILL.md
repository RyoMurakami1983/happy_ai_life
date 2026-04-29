---
name: split_multi_repo_plan
description: >
  複数リポ環境で、design-workshop のアーキテクチャ文書から
  repo ごと に独立した plan.md を生成。
  DAG validation + cycle detection + contract matching を含む。
  Use when:
  unified architecture を repo ごとの実装 plan に分割したいとき。
compatibility: "plan-generation"
---

# Split Multi Repo Plan

Design-workshop の統一アーキテクチャ文書から、リポごとに独立した plan.md を生成する sub-skill です。

複数リポ環境における依存関係の検証、循環依存の検出、提供/要求契約の照合を実施し、各リポの実装計画を独立した markdown ファイルとして出力します。

## こんなときに使う

このスキルは次のようなときに使います:

- 複数リポが関連する設計が完了し、各リポの plan.md を生成したいとき
- マルチリポ環境における依存関係の妥当性を検証したいとき
- リポ間の contract（provides/requires）が正しく合致しているか確認したいとき
- 統一アーキテクチャ文書から repo ごとに独立した plan artifact を作成したいとき

## 入力スキーマ

```yaml
unified_architecture:
  repos:
    - name: "backend"
      modules: ["api_server", "database"]
      provides:
        - artifact: "openapi"
          path: "docs/openapi.yaml"
          version: "v1"
    - name: "frontend"
      modules: ["web_ui"]
      requires:
        - source_repo: "backend"
          artifact: "openapi"
          version: "v1"
```

### 必須フィールド

- `repos`: repo 定義のリスト
- `repo.name`: リポジトリ名（一意）
- `repo.modules`: このリポが提供するモジュールのリスト

### オプションフィールド

- `repo.provides`: このリポが提供するアーティファクト（artifact, path, version）
- `repo.requires`: このリポが必要とするアーティファクト（source_repo, artifact, version）

## ワークフロー: Multi-repo plan split

### ステップ 1 — 入力と成功条件を固定する
統一アーキテクチャ、対象リポ、依存関係、生成すべき plan artifact の完了条件を確認します。

### ステップ 2 — contract と DAG を検証する
repo 間の provides / requires、循環依存、blocking dependency を確認してから repo ごとの plan を生成します。

## 出力スキーマ

各リポについて以下の構造の dict を返します：

```python
{
  "repo_name": {
    "plan_md": "# YAML Front-matter + Narrative Markdown"
  }
}
```

### plan.md フォーマット（新スキーマ - Phase 1 修正）

```markdown
---
project_context:
  repository: "backend"
  related_repositories: ["frontend", "mobile"]

dependencies:
  blocking: []
  contracts:
    provides:
      - artifact: "openapi"
        path: "docs/openapi.yaml"
        checksum: null
        version: "v1"
      - artifact: "db_schema"
        path: "schema.sql"
        checksum: null
        version: "v1"
    requires:
      - source_repo: "frontend"
        artifact: "ui_schema"
        path: "../frontend/schema.json"
        checksum: null
        version: "v1"

---

# Backend Implementation Plan

## Phase Breakdown

### Phase 1: Setup and Dependencies

#### Blocking Dependencies
- Requires `ui_schema` (v1) from `frontend`

#### Provided Artifacts
- Provides `openapi` (v1) at `docs/openapi.yaml`
- Provides `db_schema` (v1) at `schema.sql`

...
```

### スキーマの重要な変更点

1. **`dependencies.provides` → `dependencies.contracts.provides`**
   - トップレベルの `provides` が削除され、`contracts.provides` 配下に移行
   
2. **フィールド名の統一**
   - `name` → `artifact` に変更（provides/requires で統一）
   
3. **`contracts.requires` の新規追加**
   - このリポが消費する上流アーティファクトを明示
   - `source_repo`: 上流リポ名
   - `path`: 相対パス（`../source_repo/path/to/artifact`）
   - `checksum`: null（Phase 3 で計算）
   
4. **Checksum 戦略の変更**
   - **旧**: メタデータから計算した SHA256（誤った値）
   - **新**: `null`（プレースホルダー）
   - **計算時期**: Phase 3 (`contract_verify`) の初回実行で実ファイルから計算

## Core Functions

### `build_dependency_graph(repos: List[Dict]) -> Dict`

Repos から依存関係 DAG を構築。
- Input: repo list
- Output: `{"repo_name": ["dependency_1", "dependency_2"]}`

### `find_cycles(graph: Dict) -> List[List[str]]`

DFS を用いて循環依存を検出。

**エラーケース**: 循環検出時は `CircularDependencyError` を raise。

### `validate_contracts(repos: List[Dict]) -> List[str]`

Provides/Requires 契約の整合性を検証。
- 全 requires はどのリポかに provides される
- provides と requires の artifact 名とバージョンが一致

**エラーケース**: 不整合時は `ContractMismatchError` を raise。

### `calculate_checksums(provides: List[Dict]) -> List[Dict]`

アーティファクトに checksum プレースホルダーを追加。

**重要**: チェックサムは `null` として生成されます。
実ファイルのコンテンツから計算されるのは Phase 3 (`contract_verify` checkpoint) の初回実行時です。
この設計により、Phase 1 生成時に実ファイルが存在しなくても plan を生成でき、
Phase 3 で実際のファイル内容を検証できます。

### `generate_plan_md(repo: Dict, all_repos: List[Dict]) -> str`

1 リポについて YAML front-matter + narrative markdown を生成。

### `split_multi_repo_plan(unified_architecture: Dict) -> Dict[str, Dict]`

Main entry point：

1. DAG 構築
2. 循環依存検出 → CircularDependencyError
3. 契約検証 → ContractMismatchError
4. 各リポについて plan.md 生成

## Error Handling

### CircularDependencyError

循環依存が検出された場合に raise。

```python
raise CircularDependencyError(f"Circular dependency detected: {cycle_path}")
```

### ContractMismatchError

Provides/Requires 契約が合致しない場合に raise。

```python
raise ContractMismatchError(f"Contract mismatch: {error_details}")
```

## 使用例

```python
from split_multi_repo_plan.main import split_multi_repo_plan

unified_architecture = {
    "repos": [
        {
            "name": "backend",
            "modules": ["api_server", "database"],
            "provides": [
                {
                    "artifact": "openapi",
                    "path": "docs/openapi.yaml",
                    "version": "v1",
                }
            ],
        },
        {
            "name": "frontend",
            "modules": ["web_ui"],
            "requires": [
                {
                    "source_repo": "backend",
                    "artifact": "openapi",
                    "version": "v1",
                }
            ],
        },
    ]
}

result = split_multi_repo_plan(unified_architecture)

# result = {
#   "backend": {
#     "plan_md": "---\nproject_context:\n..."
#   },
#   "frontend": {
#     "plan_md": "---\nproject_context:\n..."
#   }
# }

# 各 plan_md をファイルに書き込み
for repo_name, plan_info in result.items():
    with open(f"{repo_name}/plan.md", "w") as f:
        f.write(plan_info["plan_md"])
```

## 実装詳細

### 循環依存検出アルゴリズム

Tarjan の DFS ベースアルゴリズムを使用：
- 訪問ノードセット
- 再帰スタック
- パス追跡で循環検出時に cycle を記録

### チェックサム戦略（Phase 1 修正）

**旧戦略（非推奨）**:
- Phase 1: メタデータから SHA256 を計算 → 実ファイルと不一致
- Phase 3: 実ファイルから計算 → Mismatch エラー ❌

**新戦略（推奨）**:
1. **Phase 1** (`split_multi_repo_plan`):
   - `checksum: null` を生成（プレースホルダー）
   - 実ファイルが存在しない時点でも plan 生成可能

2. **Phase 3** (`contract_verify` checkpoint - 初回実行):
   - checksum が null → 実ファイルから計算
   - 計算値を plan.md に記録（上書き）
   - 以後の実行で checksum 検証に使用

### 相対パス計算

`requires` セクションの `path` は相対パスで表現：
```yaml
requires:
  - source_repo: "backend"
    artifact: "openapi"
    path: "../backend/docs/openapi.yaml"  # ← 相対パス
    checksum: null
    version: "v1"
```

計算ロジック:
```python
relative_path = f"../{source_repo_name}/{source_artifact_path}"
```

### Markdown 生成

YAML front-matter 構造（新スキーマ）:
- `project_context`: リポ名と関連リポリスト
- `dependencies.blocking`: ブロッキング依存（実行順序の制約）
- `dependencies.contracts.provides`: このリポが生産するアーティファクト
- `dependencies.contracts.requires`: このリポが消費するアーティファクト（相対パス付き）

Narrative セクション:
- Phase breakdown
- 依存関係と提供アーティファクト
- Acceptance criteria
- 注記（「Checksums are calculated on first impl-and-ship execution」）

## 注意点

- **重複リポ名の禁止**: repo.name は一意である必要があります
- **バージョン指定**: requires/provides は version まで指定し、同じバージョンのみマッチ
- **DAG 性**: 循環依存は絶対に許可されません
- **関連リポの計算**: 直接依存と逆依存の両者を含めます

## テスト

`tests/test_split_multi_repo_plan.py` に comprehensive test suite が存在：

- `TestBuildDependencyGraph`: DAG 構築テスト
- `TestFindCycles`: 循環検出テスト
- `TestValidateContracts`: 契約検証テスト
- `TestCalculateChecksums`: チェックサム生成テスト
- `TestGeneratePlanMd`: Markdown 生成テスト
- `TestSplitMultiRepoPlan`: End-to-end テスト
- `TestErrorHandling`: エラーハンドリングテスト

実行:

```bash
pytest tests/test_split_multi_repo_plan.py -v
```

## 関連リソース

- `home-template/.copilot/skills/design-workshop/SKILL.md` — 前段：アーキテクチャ設計
- `home-template/.copilot/skills/sdd/sub_skills/from-design/SKILL.md` — 後段：design から plan 生成
- `home-template/.copilot/skills/sdd/sub_skills/from-plan/SKILL.md` — 次段：plan から impl-and-ship

## Version History

- **v0.2.0** (2026-04-27) - Phase 1 Fix: YAML Schema + Checksum Placeholder
  - Changed schema: `dependencies.provides` → `dependencies.contracts.provides/requires`
  - Changed field name: `name` → `artifact` (unified field name)
  - Added `contracts.requires` generation with relative paths
  - Changed checksum strategy: SHA256 metadata → `null` placeholder (calculated by Phase 3)
  - Updated SKILL.md documentation
  - All tests pass (14/14)
  - Ruff linting: PASS
  - Demo: PASS

- **v0.1.0** (2026-04-27)
  - Initial implementation
  - Core functions: DAG build, cycle detection, contract validation
  - Per-repo plan.md generation with YAML front-matter
  - Comprehensive unit tests (10 tests, 100% pass rate)
