# home sync再設計とrepo bootstrap安全弁の実装

## Executive Summary

- `sync-to-home.ps1` を partial-mirror 契約へ切り替え、`skills/` と `agents/` の不要物削除と template 完全一致を受け入れテストまで含めて固定できた。
- あわせて HOME から downstream repo を安全に bootstrap するため、`repo-secure-check` と `repo-bootstrap` の導線を追加した。
- 途中で `sync-to-home` の現行契約が期待と違うこと、`run_script()` が全 PowerShell script に `-SourceRoot` を渡す前提など、横断前提の見落としが出たが、事前Reviewで回収して [#63](https://github.com/RyoMurakami1983/happy_ai_life_coding_Environment/pull/63) まで進められた。

## Session Story

- `spec-workshop` と `design-workshop` の考え方で、home sync を「バグ修正」ではなく「契約変更」として整理し、削除境界と HOME bootstrap package の責務を分けた。
- 実装では `scripts/sync-to-home.ps1`、`scripts/repo-secure-check.ps1`、`happy_env.py`、README、skill docs、ADR、tests をまとめて更新し、`repo-template/` と `.github/hooks/` を HOME 配布対象に加えた。
- `deep-review-preflight` 相当の流れで別タスク review を行い、`repo-secure-check.ps1` の `-SourceRoot` 契約不足と source repo の `repo-template/.githooks` 例外不足を修正した。
- 最後に feature branch を push し、[#63 feat: home sync と repo bootstrap の安全弁を再設計する](https://github.com/RyoMurakami1983/happy_ai_life_coding_Environment/pull/63) を作成して、今回は merge せず review 待機へ入った。

## Reflection

### Keep

- 要求をすぐ実装せず、既存契約・README・テスト・ADR まで揃えて確認したことで、「想定バグ」ではなく「意図された whitelist 契約」だと見抜けた。
- `spec/design -> PLAN -> 実装 -> deep review -> PR` の順を崩さなかったため、PowerShell と Python launcher の跨ぎ変更でも破綻せず進められた。
- 受け入れ条件を `a/b.md`, `c.py`, `d/e.ps1` の削除と exact match でテストに落としたことで、今回の狙いを回帰可能な形にできた。

### Problem

- ユーザー期待と現行実装契約のずれが大きく、最初に仕様として整理し直すまで認識コストがかかった。
- `happy_env.run_script()` が新規 PowerShell script にも一律で `-SourceRoot` を渡す前提を、初回実装では取り込めていなかった。
- mother ship repo 自身の `core.hooksPath=repo-template/.githooks` という特例は、実際に smoke test するまで false negative として残っていた。

### Try

- sync 契約を変える変更では、最初に「mirror 対象 / 保護対象 / 受け入れテスト」を 1 セットで明文化してから実装へ入る。
- launcher から PowerShell script を呼ぶ追加では、共通引数契約を checklist 化して review 前に機械確認する。
- local safety valve を増やすときは、source repo 自身の特例と downstream repo の通常系を最初から対で fixture 化する。

### 5つのなぜ

1. なぜ `repo-secure-check.ps1` で review 指摘が出たか: 新規 script が `-SourceRoot` を受け取れず、launcher の既存呼び出し契約とずれていたため。
2. なぜそのずれが初回実装で見落とされたか: script 単体の責務に集中し、`happy_env.run_script()` の共通引数付与まで頭出しできていなかったため。
3. なぜそれでも merge 前に止められたか: 事前Reviewで「新規 script が既存ランタイム契約に乗るか」という横断観点を別レーンで見たため。
4. なぜさらに smoke test が必要だったか: source repo 自身の `repo-template/.githooks` 例外は code review だけでは見えず、実行時の事実確認が必要だったため。
5. なぜ次回の改善点になるか: sync / bootstrap のような運用コードは単体の見た目より既存契約の結線で壊れやすく、共通 checklist と fixture を先に持つほど再発を減らせるため。

### SMART

- **Specific**: 次に sync や bootstrap 系の変更を始めるときは、plan の段階で managed / protected 境界、共通引数契約、source repo 特例の 3 点を明記する。
- **Measurable**: 実装前に受け入れテスト項目が 3 つ以上言語化され、review で共通契約の見落とし指摘が 0 件であることを目標にする。
- **Achievable**: 今回追加した `repo-secure-check` の tests と partial-mirror の回帰テストをひな型として再利用できる。
- **Relevant**: 今回もっとも手戻りを生んだのが契約境界の見落としだったため、その入口を先に潰すことが直結して効く。
- **Time-bound**: 次回の sync / hook / bootstrap 系タスク開始時から適用する。

## Session Notes

- 使った主な skill / flow: `spec-workshop`, `design-workshop`, `deep-review-preflight`, `github-pr-workflow`, `furikaeri-practice`
- 主要変更: `sync-to-home.ps1` の partial-mirror 化、`repo-secure-check.ps1` 追加、`happy_env.py` の `repo-secure-check` / `repo-bootstrap` 導線追加、README / skill docs / ADR / tests 更新
- PR: [#63 feat: home sync と repo bootstrap の安全弁を再設計する](https://github.com/RyoMurakami1983/happy_ai_life_coding_Environment/pull/63)
- local worktree には別件の `home-template/.copilot/skills/github-issue-intake/SKILL.md` 未コミット差分が残っており、この PR には含めていない

## Next Steps

1. PR #63 の review signal を待ち、来たら `github-pr-review-response` 相当の流れで修正と返信を行う。
2. HOME 側へ配布した bootstrap package を、実際の downstream repo から直接使う運用確認を 1 回行う。
3. 今回は merge せず待機し、ユーザーの明示指示後に merge と `main` 復帰を進める。
