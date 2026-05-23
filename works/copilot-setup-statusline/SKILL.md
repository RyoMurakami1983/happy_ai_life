---
name: copilot-setup-statusline
description: >
  GitHub Copilot CLI の実験的 statusline を Oh My Posh で導入・調整する。
  こんなときに使う: .copilot に statusline.cmd / statusline.ps1 / statusline.sh / statusline.omp.json を作りたいとき、
  STATUS_LINE feature flag を安全に有効化したいとき、Python / TypeScript / Rust などの表示を追加したいとき。
compatibility: "Windows, WSL/Linux, PowerShell 7, bash, Python 3, Oh My Posh, GitHub Copilot CLI STATUS_LINE"
---

# Copilot CLI statusline を Oh My Posh で導入する

このスキルは、GitHub Copilot CLI の statusline をユーザー領域の `.copilot` に安全に追加するための手順です。
通常の shell prompt を流用せず、Copilot 用に短く、速く、スクリーンショットに出ても安全な 1 行表示を作ります。

## こんなときに使う

- Copilot CLI の下部に context 使用量や作業状況を表示したいとき
- Oh My Posh を使って Copilot CLI 専用の statusline を作りたいとき
- 既存の `settings.json` を壊さず `STATUS_LINE` を有効化したいとき
- `.NET` に加えて Python、TypeScript / Node、Rust などの開発環境表示を足したいとき
- `/usage` で見るプレミアムリクエスト情報を、将来 statusline へ出せるか判断したいとき

## ワークフロー: Statusline 導入と調整

## クイックリファレンス

| 判断 | 推奨 |
| --- | --- |
| 作成先 | Windows: `%USERPROFILE%\.copilot` / WSL/Linux: `$HOME/.copilot` |
| Copilot から呼ぶ入口 | Windows: `statusline.cmd` / WSL/Linux: `statusline.sh` |
| 表示ロジック | Windows: `statusline.ps1` / WSL/Linux: `statusline.sh` |
| 見た目 | `statusline.omp.json` |
| 設定更新 | `settings.json` をバックアップしてマージ |
| 雛形 | この skill の `assets/` をコピーする |
| 自動導入 | Windows: `scripts\install_statusline.ps1` / WSL/Linux: `scripts/install_statusline.sh` |
| usage 表示 | 安定した payload field が出るまでは `/usage` を使う |

### ステップ 1 — ゴール、成功条件、確認手段を固定する

ゴールは「Copilot CLI がローカル command を呼び、Oh My Posh で安全な 1 行 statusline を表示する」ことです。

成功条件は次のように置きます。

- `%USERPROFILE%\.copilot\statusline.cmd` がある
- `%USERPROFILE%\.copilot\statusline.ps1` がある
- `%USERPROFILE%\.copilot\statusline.omp.json` がある
- `%USERPROFILE%\.copilot\settings.json` に `statusLine.command` と `STATUS_LINE` が入っている
- サンプル payload を `statusline.cmd` に渡すと、空でない 1 行が返る

WSL/Linux の成功条件は次のように置きます。

- `$HOME/.copilot/statusline.sh` がある
- `$HOME/.copilot/statusline.omp.json` がある
- `$HOME/.copilot/settings.json` に `statusLine.command` と `STATUS_LINE` が入っている
- サンプル payload を `statusline.sh` に渡すと、空でない 1 行が返る

確認手段は、PowerShell または bash でサンプル JSON を pipe し、出力が期待する形か見ることです。

### ステップ 2 — 前提条件と既存設定を確認する

Windows では `pwsh`、`oh-my-posh`、既存の `.copilot\settings.json` を確認します。
WSL/Linux では `bash`、`python3`、`oh-my-posh`、既存の `.copilot/settings.json` を確認します。
既存設定は置き換えず、必ずマージ対象として読むようにします。

確認例:

```powershell
pwsh -NoProfile -Command '$PSVersionTable.PSVersion.ToString()'
oh-my-posh version
Get-Content -Raw "$env:USERPROFILE\.copilot\settings.json" | ConvertFrom-Json | Out-Null
```

```bash
bash --version
python3 --version
oh-my-posh version
python3 -m json.tool "$HOME/.copilot/settings.json" >/dev/null
```

なぜ: statusline は Copilot CLI の起動中に何度も呼ばれるため、前提の欠落や壊れた JSON があると表示が消えやすくなります。

### ステップ 3 — 小さな 3 ファイルを作る

作成先はユーザー領域の `.copilot` です。リポジトリへは入れません。
この skill は gist や外部ページを見なくても再実装できるように、`assets/` に標準テンプレートを同梱しています。

- `statusline.cmd`: Copilot CLI から呼ばれる Windows wrapper
- `statusline.ps1`: Windows で stdin の Copilot payload を読み、表示用の環境変数を作る renderer
- `statusline.sh`: WSL/Linux で stdin の Copilot payload を読み、表示用の環境変数を作る renderer
- `statusline.omp.json`: Oh My Posh の statusline 専用 mini theme

Windows へ手早く導入する場合:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.copilot\skills\copilot-setup-statusline\scripts\install_statusline.ps1"
```

WSL/Linux へ手早く導入する場合:

```bash
bash "$HOME/.copilot/skills/copilot-setup-statusline/scripts/install_statusline.sh"
```

手作業で導入する場合、Windows では `statusline.cmd`、`statusline.ps1`、`statusline.omp.json` を `%USERPROFILE%\.copilot` にコピーします。
WSL/Linux では `statusline.sh` と `statusline.omp.json` を `$HOME/.copilot` にコピーし、`statusline.sh` に実行権限を付けます。

```text
copilot-setup-statusline/
├── assets/
│   ├── statusline.cmd
│   ├── statusline.ps1
│   ├── statusline.sh
│   └── statusline.omp.json
└── scripts/
    ├── install_statusline.ps1
    └── install_statusline.sh
```

表示対象は、最初は次の程度に絞ります。

| 表示 | 目的 |
| --- | --- |
| Git branch | どの作業場所かを把握する |
| Tooling | `.NET`、Python、TypeScript / Node、Rust などの開発環境を見る |
| `ctx used/limit` | context の残り余裕を見る |
| gauge | context 使用率を一目で見る |
| duration | セッションの長さを見る |
| line changes | 追加・削除行数の大きさを見る |

なぜ: statusline は広くすると便利に見えますが、長すぎると肝心の会話領域を圧迫します。

### ステップ 4 — 言語表示は軽く検出する

Python、TypeScript、Rust は併記できます。
おすすめは Oh My Posh の各言語 segment に丸投げせず、`statusline.ps1` / `statusline.sh` で marker file を軽く見て、1 つの `COPILOT_STATUS_TOOLING` にまとめる方法です。

例:

```text
.NET 10.0.202 TS/Node 24.15.0 Python/uv 0.9.15 Rust 1.95.0
```

検出 marker の例:

| 言語 | marker |
| --- | --- |
| .NET | `*.csproj`, `*.sln`, `global.json` |
| TypeScript / Node | `tsconfig.json`, `package.json`, lock file |
| Python | `pyproject.toml`, `requirements.txt`, `uv.lock`, `.python-version` |
| Rust | `Cargo.toml`, `Cargo.lock` |

この skill では Python 系 marker がある repo では `uv` を優先し、`uv` が無いときだけ `python` / `python3` の実体へ落とします。
なぜ: Python の Windows Store alias のように、command が存在しても実際には使えない場合があります。また、`uv` 管理の repo で Windows と WSL の表示を揃えやすくなります。

### ステップ 5 — `settings.json` をバックアップしてマージする

編集前に必ずバックアップを作ります。
`feature_flags.enabled` が既にある場合は置換せず、`STATUS_LINE` だけを追加します。

追加する形:

```json
{
  "statusLine": {
    "type": "command",
    "command": "C:\\Users\\YOURUSER\\.copilot\\statusline.cmd",
    "padding": 1
  },
  "feature_flags": {
    "enabled": [
      "STATUS_LINE"
    ]
  },
  "experimental": true
}
```

WSL/Linux では `command` を `$HOME/.copilot/statusline.sh` にします。

なぜ: `settings.json` には plugin、hook、trusted folder など利用者固有の設定が入っているため、丸ごと上書きすると環境を壊します。

### ステップ 6 — サンプル payload で確認する

Copilot CLI を再起動する前に、command 単体で確認します。

```powershell
$sample = @'
{
  "cwd": "C:\\Users\\YOURUSER\\dev\\example",
  "context_window": {
    "current_context_tokens": 123456,
    "displayed_context_limit": 200000,
    "current_context_used_percentage": 61.7
  },
  "cost": {
    "total_duration_ms": 754000,
    "total_lines_added": 42,
    "total_lines_removed": 8
  }
}
'@

$sample | & "$env:USERPROFILE\.copilot\statusline.cmd"
```

```bash
sample='{
  "cwd": "/home/YOURUSER/dev/example",
  "context_window": {
    "current_context_tokens": 123456,
    "displayed_context_limit": 200000,
    "current_context_used_percentage": 61.7
  },
  "cost": {
    "total_duration_ms": 754000,
    "total_lines_added": 42,
    "total_lines_removed": 8
  }
}'

printf '%s' "$sample" | "$HOME/.copilot/statusline.sh"
```

空でない 1 行が返れば、Copilot CLI からも表示できる可能性が高いです。
Copilot CLI を既に開いている場合は `/restart` します。

## プレミアムリクエスト表示の扱い

プレミアムリクエストの使用量は、現時点では `/usage` で見る運用を優先します。
statusline は stdin の Copilot payload に含まれる値を出すのが安全で、未公開の保存場所や画面出力を scraping して表示するのは避けます。

将来 payload に安定した usage field が入ったら、`statusline.ps1` で `COPILOT_STATUS_USAGE` のような環境変数へ写し、`statusline.omp.json` に text segment を足します。

## おすすめの追加表示

最初から増やしすぎず、次の優先順にします。

| 優先 | 表示 | 理由 |
| --- | --- | --- |
| 高 | context 使用量と gauge | 会話の詰まり具合を判断しやすい |
| 高 | Git branch | 作業場所の取り違えを減らす |
| 中 | Tooling | .NET / Python / TypeScript / Rust の文脈をすぐ確認できる |
| 中 | line changes | セッションの変更規模を見積もれる |
| 低 | model / usage | payload が安定してから出す方が壊れにくい |

## 注意点

- **秘密情報を出さない**: statusline はスクリーンショット、録画、ログに残る可能性があります。
- **重い処理を入れない**: network access、巨大 directory scan、credential prompt が起きる segment は避けます。
- **既存設定を上書きしない**: `settings.json` はバックアップしてから object / array をマージします。
- **寿命の短い表示を固定しない**: `/usage` 由来の課金表示など、仕様が変わりやすいものは payload が安定してから追加します。

## 関連スキル

- `skill`: この skill 自体を改善・検証するときに使います。
- `furikaeri`: 実運用で見つかった表示の過不足を学びとして残すときに使います。

## 同梱リソース

- `assets/statusline.cmd`: Windows で Copilot CLI から呼ぶ wrapper template
- `assets/statusline.ps1`: Windows で Copilot payload を statusline 表示へ変換する renderer template
- `assets/statusline.sh`: WSL/Linux で Copilot payload を statusline 表示へ変換する renderer template
- `assets/statusline.omp.json`: Oh My Posh の mini theme template
- `scripts/install_statusline.ps1`: Windows で assets を `.copilot` へコピーし、`settings.json` をバックアップしてマージする helper
- `scripts/install_statusline.sh`: WSL/Linux で assets を `.copilot` へコピーし、`settings.json` をバックアップしてマージする helper
