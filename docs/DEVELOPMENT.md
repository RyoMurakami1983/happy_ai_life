# 開発ガイド

この文書は `happy_ai_life` に変更を入れる人向けの手順です。

## 前提

- Git
- Copilot CLI
- Python 3.14 以上
- `uv`
- 任意のエディタまたは IDE

## repo の構成

```text
happy_ai_life/
├── plugins/                  # Copilot plugin package
│   ├── happy-core/           # core workflow 向け
│   ├── happy-coding/         # coding workflow 向け
│   └── plugin.json           # plugin 定義
├── home-template/            # trusted local bootstrap
│   └── .copilot/             # 最小 bootstrap 用 instructions
├── repo-template/            # 対象 repo 用 template
│   ├── .github/              # Actions, hooks, instructions
│   └── .githooks/            # Git client hooks
├── docs/                     # 利用者向け文書
├── scripts/                  # sync / bootstrap script
├── tests/                    # test
├── pyproject.toml            # Python 設定
├── README.md                 # 入口
├── LICENSE                   # ライセンス
└── .editorconfig             # 編集ルール
```

この repo には主に次が入っています。

- `plugins/happy-core/` — workflow、authoring、GitHub 運用
- `plugins/happy-coding/` — 仕様、設計、実装、review
- `scripts/` — sync / bootstrap 用 script
- `home-template/` — ローカル環境再現用 template
- `repo-template/` — 対象 repo 配布用 template

## 開発の流れ

### 1. 準備

```powershell
git clone https://github.com/RyoMurakami1983/happy_ai_life.git
cd happy_ai_life
uv sync --dev
```

### 2. 設計

変更が非自明なら `/design-workshop` を使って整理します。

```powershell
copilot /design-workshop
```

### 3. 計画

PLAN mode で作業を分解します。

```powershell
copilot /plan
```

### 4. 実装

feature branch を切って変更します。

```powershell
git checkout -b feature/your-feature-name
```

#### protected path 開発時の maintenance mode

`.github/hooks/**`、`.githooks/**`、`.github/workflows/**`、`docs/TRUST_BOUNDARY.md`、`docs/HOOKS_GOVERNANCE.md` などの protected path を変更する作業では、通常の guard が `ask` または human review に止めることがあります。これは通常運用では正しい挙動です。

guard / policy / protected docs 自体を開発する場合だけ、人間が時限付き maintenance mode を有効にできます。AI が勝手に有効化してはいけません。

```powershell
.\scripts\enter-copilot-maintenance-mode.ps1 -Minutes 120
```

必須なのは `-Minutes` だけです。必要なら `-Issue`、`-Branch`、`-Reason` を補足できますが、状態ファイルの場所は常に `$HOME\.copilot\maintenance-mode.json` で固定です。期限が切れると guard は自動的に通常モードとして扱います。最大有効時間は 120 分です。

maintenance mode で緩和されるのは protected path edit の `ask` だけです。次の安全弁は維持されます。

- secret scan
- `git commit --no-verify` / `git push --no-verify` の拒否
- force push の拒否
- `git config core.hooksPath` など hook bypass の拒否
- `git reset --hard` や破壊的 command の拒否

作業後は明示的に終了します。

```powershell
.\scripts\exit-copilot-maintenance-mode.ps1
```

home sync 後は同じ script を `$HOME\.copilot\scripts\` から使えます。

### 5. 確認

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

`uv run pytest -q` は通常の開発ループ向けで、`slow` marker の付いた subprocess 統合テストを除外します。
slow test は hook / sync / wrapper の境界そのものを変更したときに、対象を絞って明示実行します。

### 6. コミット

Conventional Commits を使い、必要なら Co-authored-by trailer を付けます。

```powershell
git commit -m "feat: 変更内容"
```

### 7. レビュー

```powershell
git push origin feature/your-feature-name
gh pr create
```

## 主要コマンド

| コマンド | 用途 |
|----------|------|
| `uv sync --dev` | 依存関係を入れる |
| `uv run pytest -q` | 通常 test 実行（`slow` marker は除外） |
| `uv run ruff check .` | lint |
| `uv run ty check .` | 型確認 |
| `uv run app.py` | launcher 起動 |
| `uv run app.py home --dry-run` | home sync の差分確認 |
| `uv run app.py home` | home sync 実行 |

### test の例

```powershell
# 通常の確認（slow marker は除外）
uv run pytest -q

# 単体ファイル
uv run pytest -q tests/test_happy_env.py

# slow 統合テストを明示実行
uv run pytest -q -m slow tests/test_sync_to_home_whitelist.py

# slow も含めた全収集を明示する場合
uv run pytest -q -m "slow or not slow"

# hook parity だけ確認
uv run python -m pytest -q tests/test_git_hooks_secret_guard.py
```

Git hooks 周りを変えた場合は、`quality.yml` の `hook-parity` job と同じく `tests/test_git_hooks_secret_guard.py` を先に流します。
home sync / repo-scoped guard wrapper / PowerShell hook wrapper の境界を変えた場合は、関連する `slow` test を個別指定して確認します。

### 品質確認の例

```powershell
uv run ruff check .
uv run ty check .
```

## 品質ゲート

PR では主に次を通します。

1. **gitleaks** — secret 検出
2. **textlint** — Markdown lint（必要時のみ）

詳しくは [品質ゲート](QUALITY_GATES.md) を参照してください。

## skill / agent / instructions を作る

[作成ガイド](AUTHORING.md) を参照してください。skill 構成、agent 作成、instructions の置き場をまとめています。

## Git 運用

### branch 名の例

```text
feature/<description>
bugfix/<description>
docs/<description>
refactor/<description>
```

### commit 種別の例

```text
feat: 機能追加
fix: 不具合修正
docs: 文書更新
refactor: リファクタリング
test: test 追加
chore: 雑務
```

### PR の流れ

1. branch を切る
2. ローカルで確認する
3. push する
4. PR を作る
5. review 指摘に対応する
6. 承認後に merge する

## セキュリティの考え方

この repo では複数段の secret 保護を使います。

1. editor / IDE
2. pre-commit hook
3. pre-push hook
4. GitHub branch protection
5. GitHub Action の gitleaks

どこかで secret が見つかると処理が止まります。`gitleaks` まわりは [トラブルシューティング](TROUBLESHOOTING.md) を参照してください。

## ふりかえり

`furikaeri` skill で作業の学びを残せます。

```powershell
copilot /furikaeri
```

## 重要ファイル

| ファイル | 用途 |
|----------|------|
| `.github/copilot-instructions.md` | repo 全体の guidance |
| `pyproject.toml` | Python 設定 |
| `.gitleaks.toml` | secret 検出設定 |
| `.editorconfig` | 書式ルール |
| `.github/workflows/quality.yml` | 品質ゲート workflow |

## 関連

- [作成ガイド](AUTHORING.md)
- [品質ゲート](QUALITY_GATES.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [README](../README.md)
