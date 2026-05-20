# WSL2 開発調査

WSL2 の Ubuntu 26.04 からこの repo を開発できる範囲と、現時点で Windows に依存している範囲を整理します。

## 結論

WSL2 でも **repo 自体の編集・focused test・lint・bash/sh ベースの hook 開発に加え、home sync -> repo secure check -> sync to repo -> install git hooks の bootstrap 導線まで進められる** 状態になりました。  
現在の Linux / WSL2 導線は `sync-to-home.sh`、`repo-secure-check.sh`、`sync-to-repo.sh`、`install-git-hooks.sh` を使います。

この Ubuntu 26.04 環境では `pwsh` / `powershell` / `jq` が未導入でしたが、`uv run app.py --no-interactive` は bash / `uv` 導線で進められるようにしました。  
一方で bash variant の safety guard を実際に動かすには `jq` が必要です。

## 判定表

| 項目 | WSL2 での扱い | 根拠 |
|------|---------------|------|
| repo の編集、Python 実行、focused test、ruff | **使える** | repo は Python/uv ベースで、`tests/test_app_smoke.py` もこの環境で通る |
| repo-template の Git client hooks (`.githooks`) | **使える** | `repo-template/.githooks/*` は `#!/usr/bin/env sh` ベースで、`git` と `gitleaks` を前提にしている |
| repo の Copilot safety hook (`.github/hooks/safety-guard.json`) | **使える** | `bash` と `powershell` の両 variant を持ち、`repo-secure-check.ps1` は非 Windows host で `bash` を優先する |
| `uv run app.py` / `uv run app.py home` | **使える** | non-Windows host では `sync-to-home.sh` を選び、repo 内の `uv` で home sync を実行する |
| home sync 後の user-level guard | **使える** | `$HOME/.copilot/config.json` に bash / powershell の両 variant を持つ managed entry を書き込む |
| `repo-secure-check.sh` | **使える** | Linux / WSL2 から `.sh` で local safety valves と必要ツールを確認できる |
| `sync-to-repo.sh` | **使える** | `rsync` ベースで `.github` / `.githooks` / `policy` / `docs/furikaeri` を同期する |
| `install-git-hooks.sh` | **使える** | source repo / target repo の `core.hooksPath` 契約を維持して有効化できる |

## WSL2 で既に使えるところ

### 1. repo の日常開発

- `uv sync --dev`
- `uv run python -m pytest -q tests/test_app_smoke.py`
- `uv run ruff check .`

この repo の主要な開発サイクルは Python 側で回るため、WSL2 でも普通に進められます。

### 2. repo 配布用 Git hooks

`repo-template/.githooks/pre-commit`、`pre-push`、`lib/secret-guard.sh`、`lib/commit-safety-guard.sh` はすべて POSIX `sh` 前提です。  
したがって、target repo 側で `.githooks` が正しく配置されていれば、WSL2 の Git でも動かせます。

### 3. repo-owned Copilot hooks の bash variant

`.github/hooks/safety-guard.json` は `bash .github/hooks/scripts/guard_pre_tool.sh` と PowerShell variant の両方を持っています。  
さらに `repo-secure-check.ps1` は非 Windows host では bash variant を優先して判定するため、**repo に既に `.github/hooks` がある状態の確認ロジック自体は cross-platform を意識しています**。

ただし bash variant の `guard_pre_tool.sh` は `jq` を使うため、WSL2 側では `jq` が追加で必要です。

## Windows 依存が強いところ

### 1. `uv run app.py`

`happy_env.py` の launcher は Windows では `sync-to-home.ps1`、Linux / WSL2 では `sync-to-home.sh` を選びます。  
Linux 側の home sync 実装は repo 内の `uv` で Python module を起動し、managed file と `config.json` の managed hook entry を更新します。

そのため、PowerShell 未導入の WSL2 でも `uv run app.py --no-interactive` を起点に bootstrap を始められます。

### 2. home sync の managed surface

`sync-to-home.ps1` / `sync-to-home.sh` は `$HOME/.copilot/` に `sync-to-repo.ps1` / `.sh`、`install-git-hooks.ps1` / `.sh`、`repo-secure-check.ps1` / `.sh`、`guard_pre_tool.ps1` / `.sh` を同期します。  
また `config.json` の managed home hook entry も `bash` と `powershell` の両方を持ちます。

ただし bash variant の `guard_pre_tool.sh` は `jq` を使うため、**guard 自体を動かす host では `jq` が必要**です。

### 3. repo bootstrap script

`sync-to-repo.sh` と `install-git-hooks.sh` を追加したので、WSL2 では `robocopy` ではなく `rsync` で bootstrap を進めます。  
そのため **Linux / WSL2 では `rsync` が必須依存** です。

## ドキュメント面の現状

- `README.md`
- `docs/GETTING_STARTED.md`
- `docs/HOME_SYNC.md`
- `docs/REFERENCE.md`
- `docs/DEVELOPMENT.md`

主要導線 docs に Windows と Linux / WSL2 の両方を追記しました。  
`docs/TROUBLESHOOTING.md` にも `rsync` / `jq` 不足時の対処を追加しています。

## 現時点の実務上の切り分け

### WSL2 で進めてよい作業

- plugin / docs / policy / Python code の編集
- focused test と lint
- `.github/hooks/scripts/guard_pre_tool.sh` や `.githooks/*.sh` の開発
- repo 内に既に展開済みの hook / policy の挙動調査

### Windows 側で引き続き確認した方がよい作業

- PowerShell variant の hook / bootstrap 導線確認
- `pwsh` / `powershell` を前提にした enterprise / desktop profile の確認

## WSL2 対応で足りていないもの

1. PowerShell variant と bash variant の **長期的な feature parity 維持**
2. Linux host での **`jq` 未導入時 UX 改善**
3. `repo-secure-check.sh` と docs の **依存チェック説明の継続整備**
4. 必要なら maintenance mode まわりの **bash 導線拡張**

## 現時点の運用案

当面は **WSL2 を開発主環境としてそのまま bootstrap まで進め、PowerShell variant の最終確認だけ Windows 側で補う** 運用が現実的です。  
つまり、日常の編集・test・home sync・repo bootstrap は WSL2 で回し、Windows 側では主に PowerShell 導線の回帰確認を行うのが安全です。
