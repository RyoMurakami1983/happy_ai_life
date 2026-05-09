# Enterprise Security

## 目的

この文書は、Git hooks だけに依存しない server-side governance の最小構成をまとめる。

`happy_ai_life` では、repo-scoped hooks や local Git hooks を補助ガードとして使うが、merge 前の最終防衛線は GitHub Rulesets / Branch Protection / Required checks に置く。

## この文書で扱う範囲

- GitHub Rulesets または Branch Protection の必須設定
- Required status checks の決め方
- `gitleaks` required check の扱い
- CODEOWNERS review の必須化

この文書の対象外:

- GitHub API や CLI による自動設定
- organization policy の配布方法そのもの

## 基本方針

- **Rulesets を優先**し、使えない環境では Branch Protection を使う。
- **Direct push を禁止**し、`main` は Pull request 必須にする。
- **Required status checks** を有効にし、少なくとも `gitleaks` を required check にする。
- **CODEOWNERS review** を必須にし、保護対象の変更を人間レビューに通す。
- **force push 禁止** と **branch deletion 禁止** を有効にする。

## 必須設定一覧

| 項目 | GitHub 側の設定 | この repo の最小要件 | 理由 |
|---|---|---|---|
| Direct push 禁止 | Branch rules / Ruleset restrictions | `main` への直接 push を禁止 | local hook bypass を server-side で止めるため |
| Pull request 必須 | Require a pull request before merging | 有効 | 変更を review と required checks に通すため |
| Required status checks | Require status checks to pass | 有効 | merge 前の最終確認を強制するため |
| gitleaks required check | Status checks list | `gitleaks` を含める | secret scan を skip できないようにするため |
| CODEOWNERS review | Require review from Code Owners | 有効 | 保護対象の変更を担当者 review に通すため |
| force push 禁止 | Block force pushes | 有効 | review 履歴と保護設定の回避を防ぐため |
| branch deletion 禁止 | Block deletions | 有効 | 保護 branch の誤削除を防ぐため |

## 設定前に確認すること

1. **保護対象 branch を決める**  
   この repo では `main` を保護対象にする。

2. **required check の実名を確認する**  
   `.github/workflows/quality.yml` の job 名に合わせる。現時点の最低 required check は `gitleaks`。

3. **CODEOWNERS を先に用意する**  
   GitHub は root、`.github/`、`docs/` など複数候補を読むが、この repo では `.github/CODEOWNERS` を推奨する。

## 手順

### 1. CODEOWNERS を作る

最低限、保護対象の変更に owner が割り当たる状態を先に作る。

例:

```text
* @your-org/maintainers
.github/ @your-org/maintainers
.githooks/ @your-org/maintainers
docs/ @your-org/maintainers
```

少なくとも `.github/`、`.githooks/`、`docs/` の owner は明示する。security boundary に関わる変更を CODEOWNERS review へ確実に載せるためである。

### 2. Ruleset を作る

GitHub の **Settings → Rules → Rulesets** で branch ruleset を追加し、対象 branch を `main` にする。

必須設定:

1. **Restrict updates / direct pushes** を有効にする。
2. **Require a pull request before merging** を有効にする。
3. **Require approvals** を有効にする。
4. **Require review from Code Owners** を有効にする。
5. **Require status checks to pass** を有効にする。
6. required checks に **`gitleaks`** を追加する。
7. **Block force pushes** を有効にする。
8. **Block branch deletions** を有効にする。

推奨設定:

- stale approval の dismiss
- conversation resolution 必須
- merge queue や deployment gate がある repo では、それらも同じ ruleset に統合

### 3. Branch Protection を使う場合

Rulesets が使えない場合は **Settings → Branches → Branch protection rules** で同じ内容を設定する。

最低限そろえる項目は次の通り。

1. `main` への direct push を禁止
2. Pull request 必須
3. Required status checks を有効化
4. `gitleaks` を required check に追加
5. CODEOWNERS review を有効化
6. force push 禁止
7. branch deletion 禁止

## Required status checks の決め方

この repo では、GitHub Actions workflow 内の各 job にある `name:` フィールドの値を required checks の名前として使う。

現時点の最小構成:

- `gitleaks`

将来 `quality.yml` で `textlint` などを有効化した場合は、その job 名も required checks に追加する。  
「workflow があるが required check に入っていない」状態を残さない。

## 運用メモ

- repo-scoped hooks や local Git hooks は便利だが、これだけで security baseline を満たしたとは見なさない。
- `--no-verify`、force push、hook 無効化、secret scan 無効化を防ぐ最終レイヤーとして GitHub 側設定を維持する。
- `gitleaks` required check を外す変更は security policy を弱める変更として扱う。

## 確認方法

GitHub UI 上で次を確認する。

1. `main` に direct push できない。
2. PR なしで merge できない。
3. required checks に `gitleaks` が入っている。
4. CODEOWNERS review が required になっている。
5. force push と branch deletion が無効になっている。

補足:

- `repo-secure-check.ps1` は local bootstrap と workflow 配置の確認には使えるが、remote の Rulesets / Branch Protection 設定そのものは自動確認しない。
- したがって、この項目は GitHub UI での目視確認を source of truth とする。

## 関連

- [Enterprise Security Review](ENTERPRISE_SECURITY_REVIEW.md)
- [Trust Boundary](TRUST_BOUNDARY.md)
- [Hooks Governance](HOOKS_GOVERNANCE.md)
- [品質ゲート](QUALITY_GATES.md)
