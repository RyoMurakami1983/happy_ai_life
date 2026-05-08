# ADR: Enterprise Global Guard を repo-scoped hooks より上位に置く

- Status: Proposed
- Date: 2026-05-08
- Decision Owner: repository maintainer

## Context

`happy_ai_life` は Copilot CLI の共同作業環境を管理する repository である。

現状では、repository へ `.github/hooks/` と `.githooks/` を導入し、gitleaks や destructive command guard を実行できる。

この方針は個人利用や信頼済み repository では有効である。

しかし企業利用では、repository 内に置かれた hooks を信頼の根にすることはできない。

理由:

- repository 自体が hook 定義と hook script を変更できる。
- 悪意ある repository や侵害された repository では hook が弱体化される可能性がある。
- Git client hooks は local config に依存し、`--no-verify` で bypass 可能である。
- Copilot CLI hooks は外部 command として実行されるため、依存 tool や timeout の問題がある。
- session-continuity hooks は過去ログや Issue を instructions 化するため、prompt injection risk がある。

## Decision

Enterprise / user-level global guard を、repo-scoped hooks より上位の安全弁として扱う。

具体的には、次を採用する。

1. `$HOME/.copilot/config.json` に managed safety hook entry を持たせる。
2. `$HOME/.copilot/hooks/scripts/` に global guard script を置く。
3. repo-scoped hooks は repository 固有の補助ガードとして扱う。
4. protected path の変更は global guard で制御する。
5. GitHub Rulesets / Branch Protection / Required checks を merge 前の最終防衛線にする。
6. session-continuity hooks は標準では opt-in とする。
7. security / hooks / workflow / MCP / skills の変更は atomic issue と human review の対象にする。

## Consequences

### Positive

- 悪意ある repository による hook 弱体化の影響を減らせる。
- repository ごとに security baseline がばらつきにくい。
- Copilot CLI の作業に対して全 repository 共通の最低基準を持てる。
- 企業導入時に governance を説明しやすい。

### Negative

- user-level config の管理が必要になる。
- OS 差分、PowerShell / bash 差分への対応が必要になる。
- local developer experience が少し重くなる。
- false positive が出る可能性がある。

### Neutral

- repo-scoped hooks は廃止しない。
- Git client hooks は廃止しない。
- 既存の Repo Bootstrap 方針は補助ガードとして維持する。

## Alternatives considered

### A. repo-scoped hooks を正とする

却下。

repository が hook を変更できるため、企業利用の信頼の根としては弱い。

### B. GitHub Actions のみを正とする

却下。

GitHub Actions は merge 前の最終ゲートとして有効だが、local AI execution の直前制御にはならない。

### C. Home Sync の managed hook を正式な global guard にする

採用。

既存の `sync-to-home.ps1` が `$HOME/.copilot/config.json` に managed safety hook entry を追加する方向性を持っており、既存設計を活かせる。

## Follow-up Issues

- user-level safety hook を enterprise/global guard として正式化する。
- protected path 変更を global guard で検出・制御する。
- `permissionRequest` hook を追加する。
- `repo-secure-check.ps1` に `-Strict` を追加する。
- `ExecutionPolicy Bypass` を opt-in 化する。
- Branch Protection / Rulesets の導入手順を docs 化する。
