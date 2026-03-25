---
description: Python 向けの追加ルール
applyTo: "**/*.py"
---

# Python instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは Python の追加ルールだけを定義する。
- 既存の formatter、linter、type checker、test runner がある場合はそれを優先する。
- 公開関数と重要な内部関数には型ヒントを付ける。複雑な戻り値やコレクション型は省略しない。
- 新規コードでは、可能なら `pathlib` を `os.path` より優先する。
- 使い捨てスクリプト以外では `print` より `logging` を優先する。
- `except:` や `except Exception: pass` のような広すぎる例外処理は避ける。
- 可変デフォルト引数を使わない。必要なら `None` を受けて内部で初期化する。
- I/O と純粋ロジックを分離し、テストしやすい関数構造を優先する。
- 構造化データは `dataclass`、`Enum`、`typing` を使って意図を明確にする。
- スクリプト実行コードは必要に応じて `if __name__ == "__main__":` 配下に置く。