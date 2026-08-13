# Grill with Docs Result

## 対象

`copilot plugin update happy-core@happy-ai-life-marketplace` / `happy-coding@happy-ai-life-marketplace` が Windows 上で `Access denied` になる再発を減らすため、README と保守導線を「正規の更新導線」と「安全な復旧導線」に整理する。

## 読んだ source of truth

- `README.md`
- `docs/GETTING_STARTED.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PLUGIN_MAINTENANCE.md`
- `happy_env.py`
- `tests/test_app_smoke.py`
- `CONTEXT.md`
- User input: "再発防止と運用の安全性です。"
- User input: "OKです。今後同じ過ちが犯さないようにREADMEなどに記述するか、仕組みとして変更すべきところです。改善案を考えましょう"

## Fact

- README と `docs/GETTING_STARTED.md` では、marketplace plugin の更新取得を `copilot plugin update` に寄せている。
- `docs/TROUBLESHOOTING.md` には手動 backup / delete / reinstall の回避策があるが、利用者がそのまま安全に実行できる 1 本の repo-local command はない。
- `happy_env.py` は現状 `home` 同期だけを扱う薄い CLI launcher で、対話・非対話・dry-run の扱いがすでにある。
- 実地調査では、plugin directory 直下の create / delete は成功し、directory rename を含む `copilot plugin update` 経路だけが `Access denied` で失敗した。
- ユーザーは重要基準として **再発防止** と **運用の安全性** を選び、方針として **正規導線は維持しつつ safe repair を `app.py` サブコマンドで追加** を選んだ。

## Inference

- `copilot plugin update` 自体を置き換えるより、**正規導線はそのまま・失敗時だけ safe repair** の二段構えが、既存 docs と整合しやすい。
- safe repair は backup、対象限定、確認プロンプト、dry-run を備えた repo-local command にすると、PowerShell 手順を毎回手打ちするより事故を減らせる。
- marketplace plugin 利用者全員に repo clone を前提化するのは過剰なので、README / GETTING_STARTED では正規導線を保ち、fallback は TROUBLESHOOTING と repo 改善者向け導線から案内するのが自然。

## 解決した用語

- **正規導線**: 利用者に通常時の更新取得として案内する `copilot plugin update` の経路。
- **safe repair 導線**: 正規導線が lock / Access denied で失敗した後に使う、backup 付きの対象限定 reinstall 経路。

## 更新した docs

- `docs/grill_results/003_GRILL_WITH_DOCS_RESULT.md`

## ADR 判断

- 今回は新規 ADR は不要。repo-local fallback command の追加は戻しにくい配布構造変更ではなく、既存の正規導線を補強する運用改善だから。

## Blocking Unknown

- なし。

## 推奨される次工程

- `design-and-plan` で `app.py plugin-repair` の public interface、確認方式、docs の配置を implementation contract に落とす。
- `implement` では 1. launcher / safety guard、2. reinstall / restore ロジック、3. docs / tests の順で slice を切る。
