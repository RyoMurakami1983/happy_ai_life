# Home Sync

Home Sync は、この repo を改善する人向けに、個人の Copilot 環境へ最小 bootstrap 資産を同期する手順です。

## 使う場面

- 作者環境に近い Copilot CLI 設定でこの repo を開発したい
- `$HOME\.copilot\` に repo bootstrap 用 script を用意したい
- 変更前に dry-run で同期差分を確認したい

通常利用だけなら plugin install で十分です。Home Sync はこの repo 自体を育てる人向けです。

## 手順

いちばん手軽な入口は `uv run app.py` です。サブコマンド省略時は `home` をそのまま反映します。

[Windows: PowerShell]
```powershell
# 差分確認
uv run app.py home --dry-run

# 反映
uv run app.py
uv run app.py home
```

[Linux / WSL2: bash]
```bash
# 差分確認
uv run app.py home --dry-run --no-interactive

# 反映
uv run app.py --no-interactive
uv run app.py home --no-interactive
```

## 確認

[Windows: PowerShell]
```powershell
copilot status
Test-Path $HOME\.copilot\scripts\sync-to-repo.ps1
```

[Linux / WSL2: bash]
```bash
copilot status
test -f "$HOME/.copilot/scripts/sync-to-repo.sh"
```

## 戻し方

同期前の内容は `$HOME\copilot_archives\` に退避されます。戻す場合は、必要なファイルだけを手動で戻してください。

## 注意

- 先に必ず `--dry-run` を見ます。
- secret や live な `mcp-config.json` は同期しません。
- user-level hook wiring は `settings.json` ではなく `config.json` にだけ書きます。
- `config.json` は comment 行付きでも、先頭の `//` 前置きだけを保ったまま managed hook entry を更新します。
- Linux / WSL2 で repo bootstrap を進める場合は `bash`、`git`、`rsync` が必要です。home の bash guard を使う場合は `jq` も必要です。
- 詳細な旧説明は `archive/enterprise-hardening/docs/HOME_SYNC.full.md` に退避しています。
