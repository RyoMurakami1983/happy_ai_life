# Troubleshooting

<!-- TODO: 一般的な問題と解決方法を記述
構成：
- Installation issues
- home sync issues
- repo bootstrap issues
- Git hook issues
- Secret scanning issues
- Plugin issues

参考: 現在の README の Quality Gate セクションのトラブルシューティング（201-252行）
-->

## Installation Issues

### Issue: gitleaks not found

If the hook reports that `gitleaks` is required but cannot be found:

#### Step 1: Find the gitleaks path

**Windows:**
```powershell
where gitleaks
```

**macOS / Linux:**
```bash
which gitleaks
```

#### Step 2: Retry with GITLEAKS_BIN set

<!-- TODO: 詳細な設定手順 -->

#### Step 3: Make it permanent

<!-- TODO: Shell profile 設定 -->

## Home Sync Issues

<!-- TODO: home sync の一般的な問題 -->

## Repo Bootstrap Issues

<!-- TODO: repo bootstrap の一般的な問題 -->

## Plugin Issues

<!-- TODO: Plugin のインストール / アンインストール問題 -->

## Git Hook Issues

<!-- TODO: Git hook の一般的な問題 -->

## Other Issues

<!-- TODO: その他の一般的な問題 -->

## Getting Help

- Check [FAQ](FAQ.md) for common questions
- See [Reference](REFERENCE.md) for command reference
- Open an issue on GitHub
