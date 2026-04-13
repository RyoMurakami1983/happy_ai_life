# home sync を whitelist copy に切り替える

**日付**: 2026-04-13  
**ステータス**: 承認

---

## 背景

`sync-to-home.ps1` はこれまで `home-template/.copilot/` 全体を robocopy し、削除してはいけない runtime data や user-owned file を除外リストで守っていた。  
この方式は、新しい runtime directory や未把握の local file が増えるたびに除外更新が必要で、安全性を blacklist の網羅性に依存していた。

この repository の home sync で本当に配りたいものは限定されている。  
具体的には、skills、agents、instructions、sample の MCP 設定であり、live の `mcp-config.json` や runtime data を transport 層が判断して触る必要はない。

## 判断

- home sync は `.copilot/` 全体を robocopy しない
- home sync の tracked 対象は次の 4 つに限定する
  - `skills/`
  - `agents/`
  - `copilot-instructions.md`
  - `mcp-config.sample.json`
- `mcp-config.json` は user-owned live file として維持し、home sync では作成も上書きもしない
- `--mirror` / `-Mirror` は CLI 互換のため残すが、home sync では無視する
- 削除を伴う mirror semantics は repo sync のみに残す

## 根拠

- whitelist copy は「守る対象を列挙する」のではなく「配る対象だけを列挙する」ため、新しい runtime data の追加に強い
- home sync の責務は transport であり、HOME 側 live data の整理や削除判断まで持つべきではない
- `mcp-config.sample.json` と `mcp-config.json` を分ける既存方針と整合する
- GUI / CLI の warning を repo sync に寄せると、home sync の挙動説明が実態と一致する

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| 除外リスト方式のまま改善 | 既存実装に近い | 新しい runtime data の見落としに弱い |
| `-Mirror` を home から削除 | 誤解が減る | 既存 CLI 利用者の互換性を壊す |
| **whitelist copy + `-Mirror` 互換維持** | 安全性と互換性を両立しやすい | help と warning の説明更新が必要 |

## 運用

- `sync-to-home.ps1` は tracked directory のみ robocopy し、tracked file は個別コピーする
- `app.py` / GUI は home sync で mirror 確認を求めない
- README では repo sync の mirror 削除と home sync の whitelist copy を分けて説明する
- 新しく home に配布したい項目が増えたら、除外ではなく tracked 対象の一覧へ追加する

## 状態

承認
