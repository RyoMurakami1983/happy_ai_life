---
name: python-setup-dev-environment
description: >
  Use when: set up and run a reproducible Python dev environment with uv, ruff,
  and ty.
license: Personal
---

# python-setup-dev-environment

`uv`・`ruff`・`ty` を使って、再現可能な Python 開発環境を短い手順で整える skill です。
環境構築と日次運用の入口を 1 本にまとめ、余計な判断を減らします。

## こんなときに使う

- 新しい Python プロジェクトを立ち上げるとき
- 実行方法を `uv run` に統一したいとき
- lint / format / type-check の順序を固定したいとき
- `mypy` 前提の運用を `ty` に寄せたいとき

## ワークフロー: Python 開発環境を整える

### Step 1 — `uv` で基盤を作る

```powershell
uv init .
uv run python --version
uv add --dev ruff ty
```

`uv` を実行入口にすると、依存関係と実行環境を同じ状態で扱えます。

### Step 2 — 日次コマンドを統一する

```powershell
uv run ruff format .
uv run ruff check .
uv run ty check .
```

整形、lint、型チェックの順に回すと、差分と失敗原因が追いやすくなります。

### Step 3 — 起動チェックを行う

```powershell
# Replace main.py with your project entry script if needed.
uv run python main.py
```

`main.py` のようなエントリースクリプトがあるプロジェクトでは、`uv run` で仮想環境を起こしつつ起動確認までまとめてできます。

### Step 4 — 再現性を確認する

```powershell
uv sync
uv run ruff check .
uv run ty check .
```

別の端末や別の時点でも同じ状態に戻せるかを確認します。

## 注意点

- `python ...` の直実行を標準にしない
- `uv pip install` は通常運用にしない
- checker 固有の設定は `ty.toml` か `pyproject.toml` に寄せる

## 関連

- `skill`
- `git-commit-practices`
- `github-pr-workflow`

## FAQ

**Q: なぜ ty を使うの？**  
A: `ty` は `uv` / `ruff` と同じ Astral 系ツールで、型チェックを素早く回しやすいからです。より深い移行判断が必要な場合だけ、別の参照文書を追加します。
