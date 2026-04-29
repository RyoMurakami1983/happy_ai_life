# archiveした理由

## 背景

PR #95 / #96 で、この母艦 repo の共有配布方式は Copilot CLI plugin package と repo-owned marketplace を primary path に移行した。

これにより、過去の custom agent 前提、direct install 前提、古い session 共有フロー、旧 pptx skill archive は、現在の README / ADR / `.github/copilot-instructions.md` / `plugins/happy-ai-life` / `.github/plugin/marketplace.json` が示す運用の正本ではなくなった。

## 判断基準

今回の棚卸しでは、次の基準で扱いを分けた。

| 扱い | 基準 |
| --- | --- |
| 残す | 現行運用の source of truth、配布経路、ADR、template、test から参照されるもの |
| archive へ移動 | 歴史的価値はあるが、現在の入口や正本として読むと誤解を招くもの |
| purge | すでに archive 済みで、現行 repo 内の重複・容量・探索ノイズになっているもの |

## archive の扱い

`archive/` はローカル退避先として `.gitignore` 対象にした。今後は archive の中身そのものを Git に載せず、Git 上では旧配置からの削除と、この理由ドキュメントで棚卸し結果を残す。

理由:

- archive は過去資料・一時退避・調査用 export の置き場であり、現在の利用者が pull すべき正本ではない。
- plugin marketplace 移行後は `plugins/happy-ai-life/` と docs / ADR の現行文書を source of truth にする。
- 大きい schema や session dump を Git 履歴上の探索対象に増やさない。

## archive へ移動したもの

### `archive/docs/agent-notes/`

- `docs/agent-dispatch-options.md`
- `docs/agent-evaluation-guide.md`

理由:

- 4 師範 agent や custom agent 評価の検討メモであり、現在の配布対象は `tdd-coder` の narrow specialist と plugin 経由の skills / agents に整理済み。
- 現在の判断は `.github/copilot-instructions.md` と `docs/adr/agent-dispatch-rules.md` を優先する。
- 参照価値はあるが、`docs/` 直下にあると現行方針の正本に見えやすい。
- `archive/` は Git 管理外にしたため、リポジトリ上は旧 `docs/` からの削除として扱う。

### `archive/session-exports/`

- `copilot-session-9f2eaf15-fea9-4a4b-8351-44ef1055e4d0.md`

理由:

- Copilot CLI の生 session export で、root 直下に置くと現在の repo 構造を読みにくくする。
- 内容は履歴調査用にはローカル archive に残すが、現行 docs の正本ではない。

### `archive/home-template/.copilot/`

- `home-template/.copilot/skills/`
- `home-template/.copilot/agents/`
- `home-template/.copilot/docs/`

理由:

- reusable skills / agents の正本を `plugins/happy-ai-life/` に一本化した。
- 開発者本人も `copilot plugin install happy-ai-life@happy-ai-life-marketplace` で同じ skill / agent を入れる方針にした。
- `home-template/.copilot/` は trusted local home bootstrap の最小設定だけを持つ。`skills/`、`agents/`、`docs/` は HOME 側 user-owned surface として home sync では作成・更新・削除しない。

### `archive/home-sync-diff-planner/`

- `scripts/home_sync_planner.py`
- `home_sync_experiment.py`
- `tests/test_home_sync_experiment.py`

理由:

- `skills/` / `agents/` を home sync で差分同期するための planner と実験ハーネスだった。
- 現在は reusable skills / agents の正本を plugin package に一本化し、home sync が `skills/` / `agents/` を触らないため production path から外れた。
- 将来、同種の destructive sync 設計を再検討する場合の参考としてローカル archive に退避するが、通常の repo checkout には含めない。

## purge したもの

### `archive/skills/pptx/`

理由:

- すでに archive 済みの旧 pptx skill 一式であり、現在は plugin package / installed plugin 側の `pptx` skill を使う。
- 大量の OOXML schema と helper script を含み、repo 全体の探索ノイズと容量を増やしていた。
- 作業開始時点で削除状態になっていたため、ユーザー確認のうえ「archive 内の古い保管物の purge」として扱った。

## 残したもの

- `README.md`
- `.github/copilot-instructions.md`
- `.github/plugin/marketplace.json`
- `plugins/happy-ai-life/`
- `home-template/.copilot/copilot-instructions.md`
- `repo-template/`
- `scripts/`
- `tests/`
- `docs/adr/`
- `docs/furikaeri/`
- `docs/sessions/`
- `docs/copilot-plugin-distribution-follow-up-scope.md`

理由:

- 現行運用、配布経路、設計判断、検証の正本であるため。
- plugin marketplace 移行後も、trusted local bootstrap と repo-local bootstrap の責務境界を説明するために必要。
- `docs/sessions/` は repo hook で append-only として保護されているため、今回の archive 対象から外した。

## 今後の運用

- `docs/` 直下には、現在の読み手が最初に参照すべき文書だけを置く。
- 古い検討メモや session export はローカルの `archive/` に移す。
- archive へ移す場合は、Git には旧配置からの削除として表し、理由をこの文書へ追記する。
- archive 内でも再利用価値がなく、重複や容量が大きいものは、ユーザー確認後に purge として扱う。
