---
name: copilot-setup-statusline
description: >
  GitHub Copilot CLI の実験的 statusline を Oh My Posh で導入・調整する。
  こんなときに使う: .copilot に statusline.cmd / statusline.ps1 / statusline.sh / statusline.omp.json を作りたいとき、
  STATUS_LINE feature flag を安全に有効化したいとき、host terminal の Nerd Font / Windows Terminal font.face まで切り分けたいとき。
---

# Copilot CLI statusline を Oh My Posh で導入する

このスキルは、GitHub Copilot CLI の statusline をユーザー領域の `.copilot` に安全に追加するための手順です。
通常の shell prompt を流用せず、Copilot 用に短く、速く、スクリーンショットに出ても安全な 1 行表示を作ります。

## こんなときに使う

- Copilot CLI の下部に context 使用量や作業状況を表示したいとき
- Oh My Posh を使って Copilot CLI 専用の statusline を作りたいとき
- 既存の `settings.json` を壊さず `STATUS_LINE` を有効化したいとき
- `.NET` に加えて Python、TypeScript / Node、Rust などの開発環境表示を足したいとき

## ワークフロー: Statusline 導入と調整

最初は最小構成で 1 行表示を作り、表示速度と安全性を崩さない範囲で必要な情報だけを足していきます。

## クイックリファレンス

| 判断 | 推奨 |
| --- | --- |
| 作成先 | Windows: `%USERPROFILE%\.copilot` / WSL/Linux: `$HOME/.copilot` |
| Copilot から呼ぶ入口 | Windows: `statusline.cmd` / WSL/Linux: `statusline.sh` |
| 表示ロジック | Windows: `statusline.ps1` / WSL/Linux: `statusline.sh` |
| 見た目 | `statusline.omp.json` |
| 設定更新 | `settings.json` をバックアップしてマージ |
| アイコン描画の前提 | host terminal で Nerd Font を使う |
| 雛形 | この skill の `assets/` をコピーする |
| 自動導入 | Windows: `scripts\install_statusline.ps1` / WSL/Linux: `scripts/install_statusline.sh` |

| 利用形態 | installer の考え方 |
| --- | --- |
| Windows | Windows 側で oh-my-posh / Nerd Font / Windows Terminal `font.face` まで整える |
| WSL (Ubuntu 26.04 など) | Linux 側の statusline を作りつつ、host Windows 側の Nerd Font / Windows Terminal `font.face` も見る |
| Pure Ubuntu 26.04 server | server 側では `statusline.sh` と `oh-my-posh` を整える。font は接続元 terminal 側で扱う |

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
WSL では `bash`、`python3` 3.10 以上、`oh-my-posh`、`powershell.exe` 経由で見える host Windows Terminal、既存の `.copilot/settings.json` を確認します。
Pure Ubuntu 26.04 server では `bash`、`python3` 3.10 以上、`curl`、既存の `.copilot/settings.json` を確認します。`unzip` が無い server では direct binary download fallback で `oh-my-posh` を入れます。
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

### ステップ 2.5 — host terminal のフォントを先に切り分ける

Oh My Posh のアイコンは **statusline を動かしている OS ではなく、表示している terminal 側** で描画されます。
特に WSL では、Linux 側にフォントを足しても足りず、**Windows Terminal など host 側の `font.face`** が Nerd Font になっている必要があります。

- Windows: 今使っている terminal の profile または `profiles.defaults.font.face` を Nerd Font にする
- WSL: Windows host の terminal 設定を確認する。WSL 内にフォントを置いても glyph 崩れは直らない
- Pure Ubuntu 26.04 server: glyph は server ではなく接続元 terminal が描画する。SSH 先から接続元 terminal の font は自動変更できない
- Oh My Posh 推奨フォント: `MesloLGM Nerd Font`

インストーラーはこの点を preflight し、`oh-my-posh` が無ければ導入し、必要なら `MesloLGM Nerd Font` も入れます。
Windows Terminal の `settings.json` が見つかり、まだ Nerd Font が設定されていなければ、バックアップを作って `font.face` も自動更新します。
ただし pure Ubuntu 26.04 server の場合は host terminal に触れないため、server 側では `oh-my-posh` 導入までに留まり、font は接続元で整えます。
詳しい切り分けと設定例は `references/host-terminal-fonts.md` を参照します。

### ステップ 3 — 小さな 4 ファイルを作る

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

Windows script と WSL 上の Linux script は `.copilot` 配下のファイルを更新したあと、必要なら `oh-my-posh` と `MesloLGM Nerd Font` を導入します。
Windows Terminal の `settings.json` が見つかり、まだ Nerd Font が使われていなければ、バックアップを作ったうえで `font.face` を `MesloLGM Nerd Font` へ寄せます。
Pure Ubuntu 26.04 server では Linux script が `oh-my-posh` を user 領域へ入れ、`unzip` が無い場合は direct binary download fallback を使います。接続元 terminal の font は自動変更しません。
VS Code など Windows Terminal 以外の host terminal は自動変更しないため、その場合は手動設定が必要です。

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

表示速度を優先したい場合は、`COPILOT_STATUS_SKIP_TOOL_VERSIONS=1` を設定すると `.NET` / `TS/Node` / `Python/uv` / `Rust` のバージョン取得を省略し、外部コマンド起動回数を減らせます。

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

## おすすめの追加表示

最初から増やしすぎず、次の優先順にします。

| 優先 | 表示 | 理由 |
| --- | --- | --- |
| 高 | context 使用量と gauge | 会話の詰まり具合を判断しやすい |
| 高 | Git branch | 作業場所の取り違えを減らす |
| 中 | Tooling | .NET / Python / TypeScript / Rust の文脈をすぐ確認できる |
| 中 | line changes | セッションの変更規模を見積もれる |

## 注意点

- **秘密情報を出さない**: statusline はスクリーンショット、録画、ログに残る可能性があります。
- **重い処理を入れない**: network access、巨大 directory scan、credential prompt が起きる segment は避けます。
- **既存設定を上書きしない**: `settings.json` はバックアップしてから object / array をマージします。
- **WSL の glyph 崩れは host 側を疑う**: WSL 内のフォント追加ではなく、Windows Terminal など host terminal の `font.face` を確認します。

## 関連スキル

- `skill`: この skill 自体を改善・検証するときに使います。
- `furikaeri`: 実運用で見つかった表示の過不足を学びとして残すときに使います。

## 同梱リソース

- `assets/statusline.cmd`: Windows で Copilot CLI から呼ぶ wrapper template
- `assets/statusline.ps1`: Windows で Copilot payload を statusline 表示へ変換する renderer template
- `assets/statusline.sh`: WSL/Linux で Copilot payload を statusline 表示へ変換する renderer template
- `assets/statusline.omp.json`: Oh My Posh の mini theme template
- `scripts/install_statusline.ps1`: Windows で assets を `.copilot` へコピーし、`settings.json` をバックアップしてマージし、必要なら oh-my-posh / Nerd Font / Windows Terminal font.face を整える helper
- `scripts/install_statusline.sh`: WSL/Linux で assets を `.copilot` へコピーし、`settings.json` をバックアップしてマージし、必要なら oh-my-posh と WSL host 側の Nerd Font / Windows Terminal font.face を整える helper
- `scripts/windows_terminal_font.py`: WSL から Windows Terminal の font 設定を検査・更新する helper
- `references/host-terminal-fonts.md`: Windows / WSL で icon glyph を崩さないための host terminal font 設定メモ
