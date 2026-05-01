# 配布方針: plugin を primary、home sync を最小 bootstrap にする

**日付**: 2026-05-01  
**ステータス**: 承認

---

## 背景

この母艦 repo は、次の 3 つの配布経路を持つ。

1. 公開・共有向けの Copilot CLI plugin
2. trusted local author bootstrap としての home sync
3. 対象 repo に運用資産を入れる repo bootstrap

過去には `home-template/.copilot/` 側に skills / agents / docs を多く持たせていた時期があり、plugin install、home sync、repo sync の責務が混ざりやすかった。  
また direct repository / URL / local path install のような導線も残っており、どれを primary path とするかが文書上で揺れやすかった。

## 判断

- 公開・共有向けの **primary distribution** は `plugins/happy-core/` と `plugins/happy-coding/` の Copilot CLI plugin とする
- install の主導線は `plugin@marketplace` 形式とする
- `home-template/.copilot/` は **trusted local author bootstrap** に限定し、plugin distribution の代替にしない
- `repo-template/` は対象 repo の `.github/` / `.githooks/` を整えるための bootstrap template とする
- plugin install は repo-local instructions / hooks / Git client hooks / live config を副作用として書き込まない
- `mcp-config.json` は user-owned live file とし、母艦 repo の配布責務に含めない
- Context7 のような外部 documentation lookup は、この repo の MCP sample ではなく外部 Copilot CLI plugin として案内する

## 役割分担

| 配布経路 | 対象 | 役割 |
| --- | --- | --- |
| `plugins/happy-core/`, `plugins/happy-coding/` | 公開・共有向け reusable skills / agents | primary distribution |
| `home-template/.copilot/` | 作者本人・信頼済みローカル環境 | 最小 bootstrap |
| `repo-template/` | 対象 repo | repo instructions / workflow / hooks の初期導入 |

## 根拠

- reusable skills / agents は plugin として配った方が、install / uninstall / version 管理の境界が明確になる
- home sync に配布責務を持たせすぎると、user-owned surface と managed surface が混ざりやすい
- repo bootstrap は team repo の運用資産配布が目的であり、個人環境 bootstrap と分けた方が説明しやすい
- live `mcp-config.json` を user-owned と固定することで、外部接続設定と repo 配布資産を混同しにくくなる

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| home sync を primary path にする | 作者ローカルでは手軽 | 公開・共有向けの install 境界が曖昧になる |
| plugin install で repo-local asset まで配る | 初回導入は少ない手順で済む | repo 固有資産と共有資産の責務が混ざる |
| **plugin primary + home sync 最小 bootstrap + repo bootstrap 分離** | 配布経路ごとの責務が明確 | 導線が複数あるため文書整理が必要 |

## 運用

- README では primary path を marketplace install として示す
- 個人用の再現は Home Sync 文書へ分ける
- team repo への導入は Repo Bootstrap 文書へ分ける
- plugin 変更後の smoke test は、必要ならローカル checkout を marketplace として add して確認する

## 非目標

- plugin install だけで target repo の hooks や workflows を有効化すること
- home sync で reusable skills / agents の primary distribution を担うこと
- live `mcp-config.json` をこの repo が初期化・上書きすること

## 関連

- `docs/adr/happy-ai-life-plugin-split-and-skill-slug-simplification.md`
- `docs/adr/instruction-hierarchy-and-authoritative-source.md`
- `docs/adr/home-sync-partial-mirror-and-home-bootstrap.md`
