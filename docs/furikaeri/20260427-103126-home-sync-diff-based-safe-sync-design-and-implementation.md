# home-sync-diff-based-safe-sync-design-and-implementation

## Executive Summary

open PR #91 / #92 のレビュー対応を整理したあと、`app.py` 起点の home sync が extra skill を削除する問題を調査し、dry-run 表示不整合と mirror 設計の危険性を切り分けた。そこから `skills/` / `agents/` を filesystem diff ベースへ再設計し、PowerShell orchestration + Python planner 方式で実装した。破壊系の変更だったため、実験ハーネスを先に作ってから本実装へ入れたのが有効だった。

## Session Story

1. open PR #91 / #92 の review signal を整理し、#91 は superseded、#92 を本命として review response を完了した。
2. `app.py` 実行で `~/.copilot/skills/kintone-implement-enterprise-rest-api/` が削除される現象を調査し、削除自体は partial-mirror 仕様どおりだが、dry-run 表示が実体と一致していないことを再現付きで確認した。
3. user-owned extra skill / agent を壊さない方向へ要件を整理し、`robocopy /MIR` をやめて自前 filesystem diff を正本にする設計へ切り替えた。
4. `home_sync_experiment.py` と専用テストを先に作り、preserve / archive / replace を temp workspace 上で確認できるようにした。
5. `home_sync_planner.py` を追加し、`sync-to-home.ps1` を PowerShell orchestration + Python planner 方式へ更新した。
6. README / ADR / tests を新仕様に合わせ、実際の sync 手順と manual restore まで文書化した。

**使用した skill / tool**: `gh-pr-review-response`, `deep-research-preflight`, `design-workshop`, `furikaeri-practice`, `powershell`, `view`, `apply_patch`, `sql`

## Reflection

### Keep

- 破壊系の同期変更を、いきなり本番スクリプトで触らず実験ハーネスで先に固定したこと
- 「削除そのもの」と「dry-run 表示バグ」を分けて調査し、原因を混同しなかったこと
- `skills/` と `agents/` を同じアルゴリズムにせず、粒度差を設計に反映したこと

### Problem

- 最初の home sync 設計は `skills/` / `agents/` を managed directory とみなし、配布後の user-owned extra を壊しうる境界だった
- dry-run が robocopy ログ依存だったため、表示と実体の契約が弱かった
- 実運用手順の README 追記が実装後半まで遅れ、使い方の見え方が一時的に薄かった

### Try

- destructive 変更を含む同期ロジックは、今後も「実験ハーネス → 本実装」の順で進める
- sync 意味論を変えるときは、README に「dry-run / live / archive / restore」の運用手順を同時に書く
- user-owned extra を含む領域は、mirror 前提ではなく ownership 境界から先に設計する

### 5つのなぜ

1. なぜ extra skill が問題になったか  
   `skills/` が mirror-managed で、template に無い local asset を削除する設計だったから。
2. なぜ dry-run で防げなかったか  
   差分表示が robocopy ログの解析に依存し、`EXTRA Dir` などの表現差を十分に扱えていなかったから。
3. なぜその依存が残っていたか  
   robocopy を同期エンジンだけでなく、差分の source of truth としても使っていたから。
4. なぜ危険な設計のまま進みやすかったか  
   `skills/` / `agents/` が「配布物」でもあり「ユーザー拡張点」でもあるという ownership 境界が明文化されていなかったから。
5. どこを変えるべきか  
   destructive sync は ownership を先に定義し、差分判定は自前でテスト可能な契約に切り出すべき。

### SMART

- **S**: 次回 `sync-to-home.ps1` の仕様変更を入れるとき、`home_sync_experiment.py` に再現ケースを先に追加してから本実装へ入る
- **M**: 変更対象ごとに「preserve / update-with-archive / managed delete」の 3 パターンをテストで先に固定する
- **A**: 既存の experiment harness と planner test をそのまま拡張できる
- **R**: destructive 変更の事故防止と dry-run / live 契約の維持に直結する
- **T**: 次に home sync や repo sync の意味論を変えるタスクで実施する

## Session Notes

- `uv run app.py` の引数なし既定は `dry_run=True`
- `skills/` は skill directory 単位、`agents/` は `*.agent.md` 単位で diff 同期へ移行した
- archive は `%USERPROFILE%\copilot_archives\skills\...` / `%USERPROFILE%\copilot_archives\agents\...` に 1 世代だけ保持する
- repo 全体の `pytest` は通過したが、repo 全体の `ruff` / `ty` は今回と無関係な既存失敗が残っている

## Next Steps

- 実 home 環境で `uv run app.py home --dry-run` を実行し、新しい preview が運用上読みやすいか確認する
- 実 home 環境で live sync を 1 回流し、`copilot_archives` の配置が想定どおりか spot check する
- repo sync 側でも ownership 境界が曖昧な surface が無いかを別タスクで点検する
