---
name: initial_setup_happy_env
description: >
  この母艦リポジトリを初回セットアップし、uv・ruff・ty・Python launcher の入口を安全に整えたいとき。
license: Personal
---

# initial_setup_happy_env

この母艦リポジトリ専用の初回セットアップを、`uv` を入口にそろえて安全に始める skill です。
first-run はここで整え、steady-state は `uv run app.py` を主入口にします。

## こんなときに使う

- `uv` がまだ入っていない Windows 環境で始めたいとき
- `ruff` と `ty` を repo の dev 環境としてそろえたいとき
- PowerShell スクリプト直叩きではなく、Python launcher へ寄せたいとき
- trusted local bootstrap と plugin distribution の使い分けを確認したいとき

## ワークフロー: 母艦を初回セットアップする

### Step 0 — `uv` の有無を確認する

```powershell
uv --version
```

入っていれば次へ進みます。見つからない場合だけ Step 1 を実行します。

### Step 1 — `uv` を導入する

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

別案として `winget install --id=astral-sh.uv -e` でも構いません。
導入後は新しい端末を開き直し、`uv --version` を再確認します。

### Step 2 — repo の dev 環境を同期する

```powershell
uv sync --dev
```

この repo では `pytest`、`ruff`、`ty` を dev dependency として管理します。
個別に `pip install` せず、まず `uv sync --dev` に寄せます。

### Step 3 — launcher と品質ゲートを確認する

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

`ruff` の既存違反が残る場合は、直近変更に関係するものから最小差分で解消します。

### Step 4 — Python launcher を使う

```powershell
uv run app.py
```

CLI で home sync を直接実行する場合。

```powershell
uv run app.py home --dry-run
uv run app.py home
```

`app.py` は home sync 専用の launcher であり、`scripts\sync-to-home.ps1` を呼び出します。repo sync / hooks install は `$HOME\.copilot\scripts\` の PowerShell スクリプトを直接使います。

### Step 5 — 必要なら Context7 plugin を入れる

Context7 はこの repo の MCP config sample として配布しません。必要な場合は Copilot CLI の interactive session で外部 plugin を導入します。以下は Context7 側の marketplace plugin 構成に基づく導入例です。実行前に現在の Copilot CLI と Context7 plugin 側の案内も確認してください。

```text
/plugin marketplace add upstash/context7
/plugin install context7-plugin@context7-marketplace
```

terminal から実行する場合の等価コマンドです。

```powershell
copilot plugin marketplace add upstash/context7
copilot plugin install context7-plugin@context7-marketplace
```

## 注意点

- `uv run app.py` は steady-state 入口であり、`uv` 未導入の first-run 入口にはなりません
- live `mcp-config.json` は user-owned とし、この repo の primary distribution path にしない
- sync ロジックを Python に二重実装しない
- repo 固有の補足は `.github/copilot-instructions.md` を参照する
