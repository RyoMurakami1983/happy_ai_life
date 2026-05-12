# 品質ゲート

この repo では、PR ごとに自動チェックを流して品質を守ります。

## 品質ゲートとは

主に次を確認します。

1. **gitleaks** — secret の混入を検出
2. **hook parity** — Git hooks が Windows / macOS / Linux で同じ前提で動くか確認
3. **textlint** — Markdown の文書品質を確認（必要時のみ）

merge 前にすべて通す前提です。

## gitleaks

### 何を検査するか

- PR に含まれる staged files
- branch 上の commit 履歴
- API key、token、AWS key、password などの典型的な secret

### どう動くか

1. **pre-commit hook**  
   `git commit` 時に staged files を検査します。

2. **pre-push hook**  
   `git push` 時に push 対象 commit を検査します。

3. **GitHub Action**  
   PR 上で最終確認します。

### third-party action の扱い

GitHub Actions で third-party action を使う場合は、tag ではなく **full commit SHA で pin** します。

この repo では `gitleaks/gitleaks-action` をその対象とし、workflow では SHA の後ろに `# v2` のような comment を付けて、人間が意図した upstream tag を読めるようにしています。

更新手順:

1. upstream release tag を決める。
2. tag が指す commit SHA を確認する。
3. workflow の `uses:` を `owner/repo@<40文字SHA>` に更新する。
4. comment の tag 表記も合わせて更新する。
5. PR で変更理由と確認結果を残す。

[Windows: PowerShell]
```powershell
git ls-remote https://github.com/gitleaks/gitleaks-action "refs/tags/v2^{}"
```

### 更新方針

- **Dependabot を使える repo** では `github-actions` ecosystem を有効化し、SHA 更新 PR を人間レビューで取り込む。
- Dependabot を使わない repo でも、同等の定期見直しを行い、tag 参照へ戻さず commit SHA pinning を維持する。
- GitHub 公式 action (`actions/*`) はこの issue の pin 対象外だが、third-party action を追加する場合は最初から SHA pinning する。

### 設定

既定では gitleaks の標準ルールを使います。調整したい場合は `.gitleaks.toml` を編集してください。

1. repo ルートの `.gitleaks.toml` を編集
2. `allowlist` などを必要最小限で追加

### secret が見つかったら

1. **pre-commit hook** で落ちた  
   該当内容を修正して再 commit します。

2. **pre-push hook** で落ちた  
   該当 commit を修正して再 push します。

3. **GitHub Action** で落ちた  
   PR の内容または履歴から secret を除去し、必要なら history も整理します。

### 基本方針

- secret を commit しない
- ローカル用 secret は environment variable や `.env` を使う
- CI/CD の secret は GitHub Secrets を使う
- 誤って漏らしたら即座に rotate する

## textlint

### 有効化

必要なときだけ有効にします。

1. `.github/workflows/quality.yml` の `textlint` job を有効化
2. `.textlintrc.json` と `package.json` を用意
3. `npm install`
4. GitHub の required status check に追加

### 設定

ルールは `.textlintrc.json` で調整します。

## hook parity

### 何を確認するか

- `repo-template/.githooks/pre-commit`
- `repo-template/.githooks/pre-push`
- `repo-template/.githooks/lib/secret-guard.sh`
- Git hooks が path の空白や non-ASCII path を含む repo でも動くこと
- Windows path と POSIX path の差で hook test が崩れないこと

### どう動くか

GitHub Actions の `quality.yml` で `hook-parity` job を流し、次の 3 OS で同じ test を実行します。

- `ubuntu-latest`
- `macos-latest`
- `windows-latest`

実行する test は `tests/test_git_hooks_secret_guard.py` です。

### ローカル確認

[Windows: PowerShell]
```powershell
uv run python -m pytest -q tests/test_git_hooks_secret_guard.py
```

macOS / Linux でも同じコマンドを使います。

### 基本方針

- parity test は Git hooks 自体の portable な挙動確認であり、repo-scoped hooks を信頼の根に昇格させるものではありません。
- OS 固有の差分が見つかった場合は、hook script か test のどちらが source of truth に沿っていないかを明確にして修正します。

## ローカル hooks

### pre-commit

`.githooks/pre-commit` で staged files を検査します。

```powershell
git commit -m "docs: 手順更新"
```

### pre-push

`.githooks/pre-push` で push 対象 commit を検査します。

```powershell
git push origin main
```

### hooks を有効化

```powershell
git config core.hooksPath .githooks
```

確認:

```powershell
git config core.hooksPath
```

`.githooks` と出れば有効です。

## 困ったとき

主に次を参照してください。

- [gitleaks が見つからない](TROUBLESHOOTING.md#問題-gitleaks-が見つからない)
- [bootstrap 後に Git hooks が失敗する](TROUBLESHOOTING.md#問題-bootstrap-後すぐに-git-hooks-が失敗する)

## 関連

- [README](../README.md)
- [開発ガイド](DEVELOPMENT.md)
- [Enterprise Security](ENTERPRISE_SECURITY.md)
