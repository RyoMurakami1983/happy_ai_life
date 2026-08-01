# Verify Commands

Loop Engineering では PrivateEval より先に、機械的に判定できる検証を実行します。
このファイルは、対象 repo ごとに検証コマンドを選ぶための例です。

## 優先順位

```text
test / lint / typecheck / build / security scan > rule check > PrivateEval
```

## この repo の基本セット

この repo では、変更範囲に応じて focused check から始めます。PR 前や影響範囲が広い変更では full quality gate に広げます。

| 変更範囲 | 最初に使う確認 |
|---|---|
| plugin manifest / version | `uv run python -m pytest -q tests/test_plugin_manifest.py` |
| skill map / routing 文書 | `uv run python -m pytest -q tests/test_skill_map.py` |
| eval policy / PrivateEval | `uv run python -m pytest -q tests/test_evals_policy.py` |
| Python code | 対象 test + `uv run ruff check .` + `uv run ty check .` |

代表的なまとめ実行:

```powershell
uv run python -m pytest -q tests/test_plugin_manifest.py
uv run ruff check .
uv run ty check .
```

skill を変更した場合:

```powershell
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\<plugin>\skills\<skill-id>\SKILL.md --level L1
```

## Node.js 例

```powershell
npm test
npm run lint
npm run typecheck
npm run build
```

## Python 例

```powershell
pytest
ruff check .
ty check .
python -m build
```

## .NET 例

```powershell
dotnet test
dotnet build
dotnet format --verify-no-changes
```

## 記録欄

| コマンド | 結果 | メモ |
|---|---|---|
|  |  |  |
