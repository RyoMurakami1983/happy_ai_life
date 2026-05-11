# Repo Bootstrap（repo 初期導入）

Repo bootstrap は、対象 repo に Copilot の guidance、Git hooks、品質ゲートを追加する手順です。

**向いている人:** チーム開発の repo に、共通の運用ルールと安全弁を入れたい人。

## 概要

bootstrap を実行すると、主に次が入ります。

- `.github/copilot-instructions.md`
- `.github/hooks/`
- `.github/workflows/*.yml`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `repo-template/` 由来の設定

これらは repo にコミットされるため、チーム全員が同じ土台を使えます。

ただし、`.github/hooks/` と `.githooks/` は **repo-scoped / local の補助ガード** です。
信頼の根は user-level / enterprise-level guard と GitHub Rulesets / Branch Protection / Required checks に置きます。

## 手順

### Step 1: 現在の状態を確認

```powershell
& $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath C:\your-repo
```

次のような項目の不足を確認します。

- `.github/copilot-instructions.md`
- `.github/hooks/`
- `.github/workflows/quality.yml`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `core.hooksPath`

不足があれば次へ進みます。

### Step 2: bootstrap を反映

```powershell
# まず dry run
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath C:\your-repo -DryRun

# 反映
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath C:\your-repo

# enterprise 向け profile を使う場合
& $HOME/.copilot/scripts/sync-to-repo.ps1 -TargetRepoPath C:\your-repo -PolicyProfile Enterprise
```

`$HOME/.copilot/repo-template/` の内容を対象 repo に同期します。

### PolicyProfile の違い

| profile | 既定値 | 主な同期対象 | 意図 |
|------|------|--------------|------|
| `Default` | はい | 通常の repo bootstrap 一式。enterprise 固有の instructions は含めない | 一般的な repo bootstrap を最小構成で入れる |
| `Enterprise` | いいえ | `Default` に加えて `.github/instructions/enterprise.instructions.md` を同期 | enterprise 向けの追加 guidance を明示 opt-in で入れる |

`-PolicyProfile Enterprise` は repo 内 asset の同期範囲を切り替えるだけで、organization policy や GitHub Rulesets を自動設定するものではありません。
`Default` で再実行した場合は、以前 `Enterprise` で配った `.github/instructions/enterprise.instructions.md` も取り除かれます。

### Step 3: Git hooks を有効化

```powershell
& $HOME/.copilot/scripts/install-git-hooks.ps1 -TargetRepoPath C:\your-repo
```

`.githooks/pre-commit` と `.githooks/pre-push` を使える状態にします。

### Step 4: 反映を確認

```powershell
cd C:\your-repo
git status
git config core.hooksPath
& $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath .
```

`core.hooksPath` が `.githooks` になっていれば正常です。

CI / automation で導入漏れを失敗扱いにしたい場合は、`-Strict` を付けます。

```powershell
& $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath . -Strict
```

## 何を確認するか

| 項目 | 役割 | 問題があると |
|------|------|--------------|
| gitleaks（pre-commit） | commit 前に secret を検査 | commit が止まる |
| gitleaks（pre-push） | push 前に secret を検査 | push が止まる |
| gitleaks（GitHub Action） | PR 上で最終確認 | PR check が落ちる |
| Copilot instructions | repo 共通の guidance を渡す | guidance 不足になる |

## 注意

⚠️ **変更は repo に残る**  
ローカルだけの設定ではありません。チーム全員に効く前提で入ります。

⚠️ **repo bootstrap だけで安全性は完結しない**  
`.github/hooks/` は repository 内で変更でき、`.githooks/` は `--no-verify` で bypass できます。
そのため、`$HOME/.copilot/` の user-level guard と GitHub 側の required checks を併用してください。

⚠️ **gitleaks が必要**  
hooks を使う全員に `gitleaks` が必要です。未導入だと commit や push が止まります。

⚠️ **既存ファイルは事前確認**  
同名ファイルがある場合は dry run の結果を見て、必要なら先に退避してください。

## 調整したいとき

### instructions を調整

`.github/copilot-instructions.md` をチーム向けに編集します。

enterprise profile を使った repo では、`.github/instructions/enterprise.instructions.md` も対象になります。

### gitleaks ルールを調整

`.gitleaks.toml` を編集して、検出対象や allowlist を調整します。

### Git hooks を調整

`.githooks/pre-commit` と `.githooks/pre-push` に独自チェックを追加できます。

## 困ったとき

[トラブルシューティング](TROUBLESHOOTING.md) を参照してください。

## 関連

- [Home Sync（個人環境同期）](HOME_SYNC.md)
- [はじめに](GETTING_STARTED.md)
- [品質ゲート](QUALITY_GATES.md)
