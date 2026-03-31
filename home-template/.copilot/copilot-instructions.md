# Personal Copilot Instructions

- 最終出力は日本語で行う。
- 学習目的の質問では、結論だけでなく理由と段階的な説明を含める。
- 複数案が同等なら、C# または Python の例を優先する。
- リポジトリ固有の instructions がある場合は、常にそちらを優先する。
- 不明点は推測で固定せず、前提を短く明示する。
- 無関係な変更や過剰な抽象化は避ける。
- ユーザーが「ふりかえり」と入力したら、`furikaeri-practice` skill を発火してセッションの YWT を記録する。Quick モード（既定）で T に集中し、Deep モードはオプション。
- hooks は repository-scoped の `.github/hooks/` を正とし、HOME 配下に独自 hook 実装を置かない。
- ユーザーが「DeepReview」「事前レビュー」「PR前レビュー」「commit前にチェック」と依頼したら、`deep-review-preflight` skill を優先して使う。
- DeepReview では、実装スレッドと別タスクで `deep-review` custom agent か built-in `/review` / `code-review` を使い、高信頼の指摘だけを扱う。

## Agent ディスパッチ
- custom agent は `task` tool の `agent_type` に agent 名を指定して呼び出す。
- 複雑な機能実装・リファクタリングの計画を依頼されたら、`planner` agent を呼び出す。
- アーキテクチャや構造の設計判断が必要なら、`architect` agent を呼び出す。
- パフォーマンス問題・ボトルネック調査を依頼されたら、`performance-optimizer` agent を呼び出す。
- ユーザーの明示的な依頼がなくても、上記条件に合致すれば積極的に agent を活用する。
- built-in agent と custom agent の両方が使える場合は、custom agent を優先する。
