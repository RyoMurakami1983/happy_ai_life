# Home Sync Governance: 管理対象と user-owned surface の境界

**日付**: 2026-05-01  
**ステータス**: 承認

---

## 背景

home sync は、過去に whitelist copy、diff sync、partial mirror など複数の段階を経てきた。  
その結果、「今の home sync が何を配り、何を触らないのか」が既存 ADR を横断しないと分かりにくくなっていた。

現在の運用では、公開・共有向けの reusable skills / agents は plugin 側が正本であり、home sync は個人環境 bootstrap のための最小経路である。  
この前提に合わせて、managed surface と user-owned surface の境界を明示する必要がある。

## 判断

- home sync は `$HOME/.copilot/` 全体の mirror をしない
- home sync の正本は `home-template/.copilot/` に置く
- 現在の home sync は **最小 bootstrap** とし、主に `copilot-instructions.md` のような共通 guidance を配る
- `$HOME/.copilot/skills/`、`$HOME/.copilot/agents/`、`$HOME/.copilot/docs/` は user-owned surface として扱い、home sync では作成・上書き・削除しない
- live `mcp-config.json` は user-owned とし、home sync では上書きしない
- `config.json` は全体を上書きせず、managed safety hook entry だけを更新し、それ以外は user-owned として保持する
- repo-local hooks は home へ inert asset として搬送せず、必要な場合だけ `sync-to-repo.ps1` で target repo へ明示配布する
- user-level safety behavior は `%USERPROFILE%\.copilot\config.json` の managed entry だけを更新し、他の user-owned 設定は保持する

## managed / user-owned の切り分け

| 種別 | 例 | 扱い |
| --- | --- | --- |
| managed bootstrap | `copilot-instructions.md` | home sync が更新する |
| managed entry | `config.json` 内の特定 hook entry | 必要な entry だけ更新する |
| user-owned live config | `mcp-config.json`, `config.json` の managed entry 以外 | 保持する |
| user-owned content | `skills/`, `agents/`, `docs/` | 作成・更新・削除しない |

## 根拠

- plugin primary の現行方針では、reusable skills / agents を home sync が運ぶ理由が薄い
- home sync が user-owned surface を触ると、個人環境の拡張点を壊しやすい
- `config.json` の managed entry だけを更新する形なら、安全 behavior を保ちつつ既存設定を壊しにくい
- repo hooks は target repo に入って初めて意味を持つため、HOME へ inert asset を置くより repo bootstrap に寄せた方が責務が明確

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| home sync で skills / agents / docs まで配る | 作者ローカルでは再現しやすい | user-owned surface を壊しやすい |
| `$HOME/.copilot/` 全体を mirror する | 実装は単純 | 破壊的で運用が危険 |
| **最小 bootstrap + user-owned surface 保護** | 安全で責務が明確 | 作者ローカルの再現は plugin install と組み合わせが必要 |

## 運用

- Home Sync 文書では「個人環境 bootstrap」であることを最初に明記する
- reusable skills / agents を使う導線は marketplace install へ寄せる
- target repo の不足確認は `repo-secure-check.ps1` を単一入口とする
- repo hooks / workflows / instructions は `sync-to-repo.ps1` と `install-git-hooks.ps1` の組で配る

## 非目標

- home sync だけで team repo の安全弁まで有効化すること
- user-owned な local customization を home sync が整理・削除すること
- live MCP 設定をこの repo が管理すること

## 関連

- `docs/adr/home-sync-whitelist.md`
- `docs/adr/home-sync-partial-mirror-and-home-bootstrap.md`
- `docs/adr/instruction-hierarchy-and-authoritative-source.md`
