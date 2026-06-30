# Commit Message Template

```text
type(scope): 変更内容

Why:
- なぜこの変更が必要か
- どの問題を防ぐか
- 未来の自分やチームが知るべき判断理由

Verify:
- 実行した検証コマンド
- 結果

PrivateEval:
- 落ちた軸: なし / <軸名>
- Stop 理由: <機械判定、Critical、PrivateEval の要点>
```

## 例

```text
fix(eval): ループ停止条件を明確化

Why:
- test が落ちていても AI 評価だけで合格扱いになるリスクがあった
- 機械判定 > ルール判定 > AI 評価の優先順位を明示するため

Verify:
- uv run python -m pytest -q tests/test_plugin_manifest.py
- uv run ruff check .

PrivateEval:
- 落ちた軸: 完了条件設計力
- Stop 理由: 機械判定と Critical 要件が通り、停止条件を文書化済み
```

