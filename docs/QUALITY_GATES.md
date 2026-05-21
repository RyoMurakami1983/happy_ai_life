# 品質ゲート

HappyDefault の品質ゲートは、速く壊れにくい AI-assisted development を支えるための最小確認です。

## PR / main push の基本

[Windows: PowerShell]
```powershell
uv run python -m pytest -q tests/test_app_smoke.py tests/test_plugin_manifest.py tests/test_secret_guard_minimal.py
uv run ruff check .
```

GitHub Actions の `quality.yml` でも同じく、PR / main push ではこの軽量確認だけを自動実行します。

## 必須で守ること

- secret を混ぜない: gitleaks を使う
- format / lint の基本を崩さない: ruff を使う
- app / plugin manifest / guard の最小 smoke test を流す

## 重い確認

必要なときだけ実行します。

```powershell
uv run python -m pytest -q
uv run ty check .
```

GitHub Actions では `quality-full-manual.yml` を `workflow_dispatch` 専用の別 workflow として分離しています。PR 画面には manual 専用 job を出さず、必要なときだけ Actions 画面から full quality を手動実行します。

PR と main push では gitleaks、smoke test、ruff を実行します。full test と type check は必要なときだけ manual workflow または手元で実行します。旧 Enterprise hardening 用の重い契約テストは `archive/enterprise-hardening/tests/` に退避しています。

## gitleaks

secret が見つかった場合は、値を削除するだけでなく revoke / rotation まで行います。対応手順は [Security Policy](../SECURITY.md) を参照してください。

GitHub Actions の `gitleaks/gitleaks-action` は third-party action なので full commit SHA で pin します。更新時は upstream tag の SHA を確認してから置き換えます。
