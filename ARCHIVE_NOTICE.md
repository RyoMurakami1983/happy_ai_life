# Archive notice

## Status

このリポジトリは2026-08-22に開発を終了し、read-onlyの履歴としてアーカイブします。

開発は [RyoMurakami1983/happy-ai-work](https://github.com/RyoMurakami1983/happy-ai-work) で継続します。移行先はCodexデスクトップアプリとCodex CLIを主対象とし、旧Copilot CLI資産をそのまま複製せず、利用目的と検証境界に基づいて再設計しています。

このrepoに残るインストール、更新、skill、agentの説明は当時の履歴です。現在の導入手順として使用しないでください。

## Open Issue disposition

| Issue | 判断 | 理由 |
| --- | --- | --- |
| [#251](https://github.com/RyoMurakami1983/happy_ai_life/issues/251) | 非移植 | Windows／WSL／USB／LANをまたぐ問題は有効だが、単一の組み込み案件から公開skillへ一般化する証拠が不足している。再発時に現行repoでscenarioから再起票する。 |
| [#247](https://github.com/RyoMurakami1983/happy_ai_life/issues/247) | 非移植 | 定期監視の需要は有効だが、schedule、SSH、systemd判定、通知を一つのskillへまとめると責務が広すぎる。Codexの標準scheduled taskを先に評価し、不足が再現した場合だけ再起票する。 |
| [#212](https://github.com/RyoMurakami1983/happy_ai_life/issues/212) | 充足済み | 現行のimplementation-planとimplementがvertical slice、RED command、期待失敗理由、RED／GREEN evidenceを扱う。docs-only等で形だけのTDDを要求しない例外も定義済み。 |
| [#211](https://github.com/RyoMurakami1983/happy_ai_life/issues/211) | 廃止・非移植 | 旧gh-pr wrapper前提の解決策は、CodexのGit指示とGitHub pluginを使う現行方針に合わない。PR templateが必要になった場合は対象repoの設定として新規に判断する。 |

## Pull requests

アーカイブ判断時点でopen pull requestはありません。

## Preservation policy

commit、closed issue、release、docsは移行せず、このrepoに履歴として保持します。新しいbacklogは移行先で、現在の構造とAcceptance Criteriaに合わせて新規作成します。
