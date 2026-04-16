# Executive Summary

.NET / WPF と外部依存の扱いで見えた出戻り要因を整理し、repo template の guidance を入口 routing と path-specific instructions に分割して強化した。repo-wide には `dotnet` を思い出す導線を置き、XAML 固有の罠と外部依存境界の罠は別ファイルへ切り出した。これにより、道具の想起と point-of-use の注意点を混ぜずに再利用できる形へ寄せられた。

# Session Story

1. 先行セッションのふりかえりから、.NET / WPF 案件で dotnet 系 skill を入口で使わなかったことが出戻り要因だと整理した。
2. その原因を、skill 名ではなく「どの状況で何を思い出すか」の導線不足として捉え直した。
3. 内部 source of truth と外部の一般論を見比べ、repo-wide instructions は全体 routing、path-specific instructions は局所ルールに分ける方針を固めた。
4. `repo-template/.github/copilot-instructions.md` に `.NET / WPF / XAML` で `dotnet` を思い出す routing を追記した。
5. `xaml.instructions.md` を新設し、binding、MVVM、OneWay / TwoWay、focus 奪取時の fallback などの局所ルールを追加した。
6. `infrastructure.instructions.md` を新設し、Serial / VISA / database / LAN / DAQ / ADC / DAC / OS API など外部依存境界の安全ルールを追加した。
7. 変更を commit / push し、PR を作成した上で、このふりかえりを同じ branch に積む流れに整えた。

# Reflection

## Keep

- 先に結論を決め打ちせず、`skill か instructions か` の責務分担を調査してから手を入れられた。
- 「道具を思い出す」と「実装時の罠を避ける」を別レイヤーに分けたため、template の再利用性が上がった。
- XAML と infrastructure を分離したことで、WPF 固有の問題と実機・外部依存の問題を混線させずに整理できた。

## Problem

- 入口 routing の不足は repo-wide 側に置くべきだったが、最初は skill 名や C# instructions の修正に意識が寄りやすかった。
- 外部依存の範囲が広いため、rules を大きく書きすぎると path-specific instructions が抽象化しすぎるリスクがあった。
- PR 作成とふりかえり保存の順序を最初から固定していなかったため、作業の節目がやや曖昧になりかけた。

## Try

- repo-wide instructions には「どの道具を先に思い出すか」だけを書き、実装罠は path-specific instructions へ逃がす分業を維持する。
- 新しい instructions を増やすときは、技術単位ではなく「どの時点で効く注意か」で分割する。
- 外部依存の強い案件では、fake / factory / simulation / safety guard を設計初期から前提にする。
- PR を開く作業では、本文作成後にふりかえり文書も同じ branch へ積む流れを標準化する。

## 5つのなぜ

1. なぜ `.NET のベストな入口` が効かなかったか。技術選定より前に、道具想起の導線が明示されていなかったから。
2. なぜ導線が明示されていなかったか。repo-wide と path-specific の責務分担が template 上で薄かったから。
3. なぜそれが問題になったか。実装時に WPF の binding 罠と外部依存の safety guard を別々に思い出せなかったから。
4. なぜ別々に思い出せなかったか。C# 全般の rules に寄せると局所的な注意が埋もれ、skill 名の議論だけでは point-of-use の助けにならないから。
5. どこを変えるべきか。repo-wide には routing、XAML には View 固有の罠、infrastructure には外部依存境界の罠を置く構造へ変えるべき。

## SMART

- **Specific**: 今後の template では、repo-wide に tool routing、path-specific に局所ルールを置く構成を維持する。
- **Measurable**: `.NET / WPF / XAML` 案件で `dotnet` routing が明示され、XAML / infrastructure の instructions が存在する状態を標準とする。
- **Achievable**: 既存 template への追記と新規 instructions 追加だけで実現できる。
- **Relevant**: .NET / WPF と外部依存の案件で生じやすい出戻り、実装忘れ、安全配慮漏れの再発防止に直結する。
- **Time-bound**: 次の desktop / hardware 連携案件からこの template を適用し、初手の道具選択と safety guard の想起が改善したかを見る。

# Session Notes

- 使った skill: `github-pr-workflow`, `furikaeri-practice`
- 調査に使った source: repo 内 template、skill 定義、GitHub custom instructions の公式ドキュメント、一般的な checklist 運用の公開知見
- 変更した template: `repo-template/.github/copilot-instructions.md`, `repo-template/.github/instructions/xaml.instructions.md`, `repo-template/.github/instructions/infrastructure.instructions.md`
- 先行改善として関連した skill: `home-template/.copilot/skills/sdd`, `home-template/.copilot/skills/repo-onboarding`

# Next Steps

1. PR レビューで guidance の粒度や `applyTo` の妥当性を確認する。
2. 次の .NET / WPF 案件で、`dotnet` routing が初手で機能するかを見る。
3. 外部依存の強い repo で `infrastructure.instructions.md` の適用範囲が広すぎないかを確認し、必要なら分割する。
