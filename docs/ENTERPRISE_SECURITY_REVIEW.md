# Enterprise Security Review for Copilot CLI Collaboration

## 目的

この文書は、`happy_ai_life` を企業利用にも耐える Copilot CLI 共同作業環境へ強化するための Reference である。

この文書は実装指示そのものではなく、Issue 作成・PR レビュー・Copilot CLI への作業依頼時に参照する判断基準として使う。

## 背景

`happy_ai_life` は、Copilot CLI の plugin、skills、agents、home sync、repo bootstrap、hooks、品質ゲートを管理する母艦 repository である。

現状の構成には良い点が多い。

- Home Sync と Repo Bootstrap が分離されている。
- `repo-template/` により既存 repository へ guidance / hooks / workflow を導入できる。
- pre-commit / pre-push / GitHub Actions による gitleaks 多層防御がある。
- `sync-to-repo.ps1` は `HooksMode = SafetyOnly` を既定にし、session-continuity hooks を標準配布しない。
- `sync-to-home.ps1` は `$HOME/.copilot/config.json` に managed safety hook entry を追加する方向性を持っている。

一方、企業利用では次の点を明確化する必要がある。

- repo-scoped hooks を信頼の根にしない。
- user-level / enterprise-level guard を最上位の安全弁にする。
- repo-local skill / MCP / instruction / hook を無条件に信用しない。
- hooks の fail-open 性質を前提に、多層防御で補う。
- Git hooks は bypass 可能であるため、GitHub Rulesets / Branch Protection / Required checks を最終防衛線にする。

## 重要な前提

GitHub Copilot CLI の hooks は外部コマンドとして実行され、repository の `.github/hooks/*.json` から自動ロードされる。

また、Copilot CLI には `preToolUse` と `permissionRequest` という制御点がある。

- `preToolUse`: tool 実行直前に allow / deny / ask / modifiedArgs を返せる。
- `permissionRequest`: permission service より前に allow / deny を返せる。

Copilot CLI hooks では `bash` / `powershell` だけでなく、`create` / `edit` / `view` / `web_fetch` なども hook matching の対象 tool name として定義されている。

参考:

- GitHub Copilot CLI hooks reference  
  https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference
- GitHub Copilot CLI command reference  
  https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference

## 結論

企業向けの基本方針は次の通り。

1. repo-scoped hooks は補助ガードであり、信頼の根ではない。
2. user-level / enterprise-level guard を最上位の安全弁にする。
3. protected path の変更は global guard で制御する。
4. Git hooks は便利だが bypass 可能なので、GitHub Rulesets / Branch Protection / Required checks を必須化する。
5. session-continuity hooks は prompt injection risk があるため標準では opt-in にする。
6. repo-local skills / MCP / instructions は L7 / 中の参照情報として扱う。
7. security policy を弱める変更は atomic issue と human review の対象にする。

## 改善対象の分類

### P0: 先に直すべき土台

- home instructions の Hooks 方針を user-level guard 優先へ修正する。
- repo-scoped hooks は信頼の根ではなく補助ガードであることを明文化する。
- user-level safety hook を enterprise/global guard として正式化する。
- protected path 変更を global guard で検出・制御する。
- `repo-secure-check.ps1` に `-Strict` を追加し、失敗時に non-zero exit する。
- hook 実行に必要な依存ツールの preflight check を追加する。
- `ExecutionPolicy Bypass` の既定使用をやめ、opt-in 化する。

### P1: 企業利用で必須に近い強化

- `permissionRequest` hook を追加して tool 許可前の安全確認を行う。
- `edit` / `create` tool による protected path 書き換えを監視する。
- Git hook 無効化につながる Git コマンドを guard に追加する。
- 危険コマンド blocklist を企業利用向けに拡張する。
- GitHub Actions の third-party actions を SHA pinning する。
- Branch Protection / Rulesets の必須設定手順を docs 化する。
- `SECURITY.md` を追加し、secret 漏洩時の対応手順を定義する。
- MCP server 追加・変更を governance 対象として docs 化する。
- repo-local skills の `allowed-tools: "*"` を禁止または警告する policy を追加する。

### P2: 保守性・運用性の強化

- `managed-manifest.json` を追加し、home sync の管理対象を明示する。
- `sync-to-repo.ps1` に `-PolicyProfile Enterprise` を追加する。
- session-continuity hook 由来の prompt injection 対策を強化する。
- Windows / macOS / Linux の hook parity を確認するテストを追加する。
- enterprise 向け導入手順を `docs/ENTERPRISE_SECURITY.md` にまとめる。

## Keep する設計

### Home Sync と Repo Bootstrap の分離

Home Sync は user-level の最小 bootstrap を扱い、Repo Bootstrap は repository へ guidance / hooks / workflow を導入する。この分離は維持する。

### `HooksMode = SafetyOnly`

session-continuity hooks を既定で配布しない設計は維持する。sessionStart / sessionEnd は便利だが、Issue、ふりかえり、過去ログを instructions 化するため prompt injection risk がある。

### gitleaks の多層防御

pre-commit、pre-push、GitHub Actions で gitleaks を使う方針は維持する。ただし、Git hooks は bypass 可能であるため GitHub 側の required check と組み合わせる。

### 日本語主体の instructions

日本語での説明、README / docs / ADR / Issue / PR 本文の日本語既定は維持する。企業利用でも、チームが日本語話者なら判断理由を日本語で残す方が運用しやすい。

## Copilot CLI へ依頼するときの原則

- 1 Issue = 1 branch = 1 PR を原則にする。
- Issue 本文に Reference / 実装範囲 / 非対象 / 完了条件 / 確認コマンドを書く。
- Copilot CLI には「対象 Issue を 1 件だけ解決する」と明示する。
- security / hooks / workflow / MCP / skills を触る Issue は人間レビュー必須にする。
- Reference と矛盾する実装をしない。
- 実行できる検証は実行し、できない場合は理由を書く。

## 共通確認コマンド

[Windows: PowerShell]
```powershell
$ uv run pytest -q
$ uv run ruff check .
$ uv run ty check .
```

[Windows: PowerShell]
```powershell
$ & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath .
```

Issue によっては `-Strict` 追加後に次を使う。

[Windows: PowerShell]
```powershell
$ & $HOME/.copilot/scripts/repo-secure-check.ps1 -TargetRepoPath . -Strict
```
