# home sync を whitelist copy に切り替える

**日付**: 2026-04-13  
**ステータス**: 承認

---

## 背景

`sync-to-home.ps1` はこれまで `home-template/.copilot/` 全体を robocopy し、削除してはいけない runtime data や user-owned file を除外リストで守っていた。  
この方式は、新しい runtime directory や未把握の local file が増えるたびに除外更新が必要で、安全性を blacklist の網羅性に依存していた。

この repository の home sync で本当に配りたいものは限定されている。  
具体的には、skills、instructions、furikaeri docs、最小限の narrow agent であり、live の `mcp-config.json` や runtime data を transport 層が判断して触る必要はない。

## 判断

- home sync は `.copilot/` 全体を robocopy しない
- home sync の tracked 対象は次に限定する
  - `skills/`
  - `docs/furikaeri/`
  - `copilot-instructions.md`
  - `agents/tdd-coder.agent.md`
- `mcp-config.json` は user-owned live file として維持し、home sync では作成・上書き・削除しない
- `mcp-config.sample.json` は配布しない。Context7 が必要な場合は外部 Copilot CLI plugin として導入する
- `--mirror` / `-Mirror` は CLI 互換のため残すが、home sync では無視する
- 削除を伴う mirror semantics は repo sync のみに残す

## 根拠

- whitelist copy は「守る対象を列挙する」のではなく「配る対象だけを列挙する」ため、新しい runtime data の追加に強い
- home sync の責務は transport であり、HOME 側 live data の整理や削除判断まで持つべきではない
- MCP config sample の配布をやめることで、外部 tool 接続の live 設定を repo 側の bootstrap と混同しない
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

## 補遺: Phase 2 — custom agent 全廃

2026-04 の Phase 2 で custom agent 配布を終了したため、tracked 対象から `agents/` を外した。  
home sync は既存の `%USERPROFILE%\.copilot\agents\` を削除せず、legacy directory が残っている場合は手動 cleanup を促す warning を出す。

## 補遺: Phase 3 — `tdd-coder` だけ再導入

2026-04 の Phase 3 では、`/fleet` または明示指名で使う narrow specialist として `agents/tdd-coder.agent.md` だけを tracked file として戻した。  
ただし home sync が配る custom agent はこの 1 体だけとし、`agents/` 配下の他ファイルは削除せず warning で手動 cleanup を促す。

## 補遺: Phase 4 — MCP config sample 配布撤退

2026-04-29 の Copilot CLI plugin 配布方式移行で、`mcp-config.sample.json` は home sync の tracked 対象から外した。

live `%USERPROFILE%\.copilot\mcp-config.json` は引き続き user-owned file とし、home sync は作成・上書き・削除しない。Context7 はこの repo の MCP sample ではなく、外部 Copilot CLI plugin として案内する。

## 補遺: Phase 5 — skills / agents / docs の plugin source-of-truth 化

Copilot CLI plugin marketplace 方式を primary path にしたため、開発者自身も reusable skills / agents は plugin install で取り込む方針に変更した。

これにより、home sync の tracked 対象から `skills/`、`agents/`、`docs/furikaeri/` を外した。`home-template/.copilot/` は `copilot-instructions.md` だけを持つ最小 bootstrap とし、HOME 側の `skills/`、`agents/`、`docs/` は user-owned surface として作成・更新・削除しない。

## 補遺: Phase 6 — HOME への `.github/hooks` 搬送を終了

2026-04 の hook 再設計で、home sync が `$HOME/.copilot/.github/hooks` に母艦 `.github/hooks` を置く挙動を終了した。

理由は、この場所が公式の user-level hook 置き場である `$HOME/.copilot/hooks` ではなく、そのままでは hook として実行されない inert bootstrap asset だったためである。repo-scoped hooks は `sync-to-repo.ps1` の明示配布に寄せ、generic な safety behavior は plugin hook として検証してから配布する。

## 状態

承認
