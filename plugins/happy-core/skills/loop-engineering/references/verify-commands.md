# Verify Commands

Loop Engineering では PrivateEval より先に、機械的に判定できる検証を実行します。
このファイルは、対象 repo ごとに検証コマンドを選ぶための例です。

## 優先順位

```text
test / lint / typecheck / build / security scan > rule check > PrivateEval
```

## この repo の例

```powershell
uv run python -m pytest -q tests/test_plugin_manifest.py
uv run ruff check .
uv run ty check .
```

skill を変更した場合:

```powershell
uv run python plugins\happy-core\skills\copilot-authoring\_skill\_eval\scripts\validate_skill.py plugins\<plugin>\skills\<skill-id>\SKILL.md
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

