# Quality Gates Configuration

<!-- TODO: 品質ゲートの詳細を記述
構成：
- GitHub Actions の品質ゲート
- gitleaks の設定とカスタマイズ
- textlint の有効化
- ローカルフック（pre-commit / pre-push）
- トラブルシューティング

参考: 現在の README の Quality Gate セクション（179-252行）
-->

## GitHub Actions Quality Gate

This repository uses GitHub Actions to check every PR.

### Always Enabled

- **Secret detection** (gitleaks)

### Optional

- **Markdown lint** (textlint)

## Secret Detection (gitleaks)

### Default Behavior

By default, gitleaks scans for secrets using its built-in rules.

### Customizing gitleaks allowlist

Edit `.gitleaks.toml` to add allowlist entries for documentation placeholders that should not be treated as secrets.

<!-- TODO: .gitleaks.toml の例 -->

## Markdown Linting (textlint)

### Enabling textlint

1. Uncomment the `textlint` job in `.github/workflows/quality.yml`
2. Copy `.textlintrc.json` and `package.json` from the quality-gate-setup skill
3. Run `npm install`
4. Add `textlint` as a required status check in Branch Protection settings

<!-- TODO: 詳細ステップ -->

## Local Pre-commit Hooks

### gitleaks

The `pre-commit` hook runs gitleaks on staged content before committing.

### pre-push Hook

The `pre-push` hook runs gitleaks on the push range before pushing.

<!-- TODO: ローカルフック設定の詳細 -->

## Troubleshooting

See [Troubleshooting](TROUBLESHOOTING.md) for common issues and solutions.

## See also

- [README](../README.md)
- [Development](DEVELOPMENT.md)
