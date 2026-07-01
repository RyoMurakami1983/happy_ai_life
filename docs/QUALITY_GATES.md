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
- privateEval の raw artifact を混ぜない: `tests/test_evals_policy.py` を使う

## 重い確認

必要なときだけ実行します。

```powershell
uv run python -m pytest -q
uv run ty check .
```

GitHub Actions では `quality-full-manual.yml` を `workflow_dispatch` 専用の別 workflow として分離しています。PR 画面には manual 専用 job を出さず、必要なときだけ Actions 画面から full quality を手動実行します。

PR と main push では gitleaks、smoke test、ruff を実行します。full test と type check は必要なときだけ manual workflow または手元で実行します。旧 Enterprise hardening 用の重い契約テストは `archive/enterprise-hardening/tests/` に退避しています。

## skill / prompt 評価

| 入口 | 測るもの | 使うタイミング |
| --- | --- | --- |
| `skill-eval` | skill / prompt の評価方法選択 | skill の挙動や指示を変えるとき |
| `empirical-prompt-tuning` | 別実行者に伝わる明瞭性 | 指示文の曖昧さを疑うとき |
| `loop-engineering` | Observe から PrivateEval までの改善ループ | 単発ではなく改善を回すとき |
| privateEval | secret なしの再利用可能な評価ケース | repo に残せる回帰ケースを育てるとき |

PrivateEval の詳細は [PrivateEval](PRIVATE_EVAL.md) を参照します。PR 常時 gate にはせず、skill / prompt / workflow の挙動を変える PR で focused eval として使います。

## gitleaks

secret が見つかった場合は、値を削除するだけでなく revoke / rotation まで行います。対応手順は [Security Policy](../SECURITY.md) を参照してください。

GitHub Actions では `gitleaks` の公式 release tarball を workflow 内で取得して実行します。PR で GitHub API 認証に依存しすぎず、repo 履歴をそのまま走査できる形を優先します。
