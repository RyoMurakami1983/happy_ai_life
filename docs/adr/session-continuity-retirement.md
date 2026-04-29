# session continuity hooks を標準運用から封印する

**ステータス**: 承認

## 背景

`sessionStart` / `sessionEnd` hooks は、前回の作業文脈を repo-local に残すために `.github/sessions/` と `.github/instructions/session-context.instructions.md` を生成していた。

しかし実運用では、repo ごとの配布と生成物管理が重く、あまり活用されなかった。さらに Copilot CLI には公式 session data、`/resume`、`/chronicle`、`/share` が整ってきたため、repo-local hook で毎回文脈を注入する責務は重複し始めた。

## 判断

- `sessionStart` / `sessionEnd` による repo-local continuity は標準運用から封印する。
- `sync-to-repo.ps1` の既定 hook 配布は `SafetyOnly` とし、`session-continuity.json` は除外する。
- legacy repo が必要とする場合だけ `sync-to-repo.ps1 -HooksMode All` で明示 opt-in する。
- `sync-to-home.ps1` は `$HOME/.copilot/.github/hooks` へ hooks を搬送しない。
- 組織利用の文脈継承は、`furikaeri-practice` による 1 日 1 回の横断ふりかえりを主導線にする。

## 根拠

- `$HOME/.copilot/.github/hooks` は公式の user-level hooks path ではなく、home sync で置いても hook として実行されない。
- hooks は同期実行であり、重い要約や共有文書生成には向かない。
- `/chronicle` は experimental だが、session store を使った横断的な standup summary に適している。
- `/share file session` は raw session export として使えるが、既定で gist 共有すべきではない。
- 日次ふりかえり skill は、保存前に公開配慮を確認でき、repo ごとの生成物を増やさない。

## トレードオフ

| 選択肢 | 利点 | 欠点 |
| --- | --- | --- |
| sessionStart/sessionEnd を標準継続 | repo ごとの自動文脈注入が強い | 配布が重く、生成物が増え、横断ふりかえりに弱い |
| 全部 plugin hook 化 | install path は単純 | 任意 repo に `.github/*` を作るリスクが高い |
| **SafetyOnly + 日次ふりかえり** | safety を残しつつ、文脈継承を明示的で横断的にできる | `/chronicle` が experimental の間は fallback が必要 |

## 運用

- 通常の repo bootstrap は `sync-to-repo.ps1` 既定の `SafetyOnly` を使う。
- session continuity hooks が必要な legacy repo は `-HooksMode All` を明示する。
- 1 日の終わりに `furikaeri-practice` を実行し、`~/.copilot/docs/furikaeri/` に日次記録を保存する。
- raw session を残す必要があるときだけ `/share file session [PATH]` を使う。
- `/share gist` や OpenTelemetry content capture は、明示的に必要な trusted environment でのみ使う。
