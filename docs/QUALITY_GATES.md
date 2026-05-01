# 品質ゲート

この repo では、PR ごとに自動チェックを流して品質を守ります。

## 品質ゲートとは

主に次を確認します。

1. **gitleaks** — secret の混入を検出
2. **textlint** — Markdown の文書品質を確認（必要時のみ）

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
