# happy_ai_life

> 楽しく AI と続ける仕事・学習・コーディングの型を、いつでもどこでも再現できるようにする。

Copilot CLI の reusable skills、agents、repo bootstrap 資産を管理する母艦リポジトリです。

## 🌱 迷ったらこれだけ

- **通常利用:** [はじめに](docs/GETTING_STARTED.md#パス-1-通常利用marketplace-plugin) から plugin を入れる
- **この repo を改善:** [開発ガイド](docs/DEVELOPMENT.md) を開き、`to-prd` → `design-and-plan` → `implement` へ進む
- **既存 repo に導入:** [はじめに](docs/GETTING_STARTED.md#パス-3-既存-repo-に導入するteam-repo-setup) の Team Repo Setup を使う
- **調査から follow-up まで回す:** 単発修正で終わらせたくないときは `loop-engineering` を起点にする

## 🚀 クイックスタート

### インストール

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

日常利用は [はじめに](docs/GETTING_STARTED.md) だけ読めば始められます。

### Plug-in の更新

```powershell
copilot plugin list
copilot plugin update happy-core@happy-ai-life-marketplace
copilot plugin update happy-coding@happy-ai-life-marketplace
```

公式 docs 上、installed plugin の更新取得は `copilot plugin update` が正規の導線です。更新通知の自動配信は前提にせず、`copilot plugin list` で version を見て、必要に応じて `copilot plugin update` を実行してください。
この repo では、利用者が見る個別 plugin version の正本は `plugins/*/plugin.json`、`.github/plugin/marketplace.json` はその配布メタ情報をそろえる mirror として扱います。

### 配布対象と `works/` の違い

- marketplace / installed plugin として配布される正本は `plugins/happy-core/` と `plugins/happy-coding/` です
- `works/` は常用前の試作、単発寄りの作業物、配布前の実験置き場です
- そのため `works/` 配下の skill は `~/.copilot/installed-plugins/...` には自動で現れません
- `works/` で育てたものを常用・再利用したくなった段階で、`happy-core` または `happy-coding` へ昇格させます

## 📚 ドキュメント

| 目的 | ドキュメント |
|------|--------------|
| 最短で使い始める | [はじめに](docs/GETTING_STARTED.md) |
| この repo を変更する | [開発ガイド](docs/DEVELOPMENT.md) |
| WSL2 での現状を確認する | [WSL2 開発調査](docs/WSL2_DEVELOPMENT.md) |
| 確認方針を見る | [品質ゲート](docs/QUALITY_GATES.md) |
| skill / agent / instructions を作る | [作成ガイド](docs/AUTHORING.md) |
| skill の地図を見る | [Skill Map](docs/SKILL_MAP.md) |
| privateEval の方針を見る | [PrivateEval](docs/PRIVATE_EVAL.md) |
| skill / privateEval の整理計画を見る | [Skill Ecosystem Action Plan](docs/SKILL_ECOSYSTEM_ACTION_PLAN.md) |
| よくある質問を見る | [FAQ](docs/FAQ.md) |
| 困ったとき | [トラブルシューティング](docs/TROUBLESHOOTING.md) |

## 🔧 この repo を変更するとき

この repo には Copilot CLI plugin、bootstrap script、品質確認用ツールが入っています。

1. **前提整理** — `to-prd` で要件・既存 docs・判断を確認する
2. **改善ループ化** — 失敗ログ、review、既知課題をまとめて扱うなら `loop-engineering` で stop rule まで固定する
3. **試作** — 不確実性が高い場合だけ `prototype` で小さく検証する
4. **設計** — 必要に応じて `design-and-plan` で構造判断と plan の土台を固める
5. **実装** — `implement` で実装と完了処理を進める
6. **確認** — 変更範囲に合う focused check を流す

```powershell
uv run python -m pytest -q tests/test_app_smoke.py tests/test_plugin_manifest.py tests/test_secret_guard_minimal.py
uv run ruff check .
```

詳しくは [開発ガイド](docs/DEVELOPMENT.md) を参照してください。

## ✅ 品質ゲート

この repo では `HappyDefault` を既定にし、PR は smoke test と ruff を優先します。full quality は必要なときに manual workflow で実行します。
`HappyDefault` は「毎回ちゃんとする」ためではなく、「毎回つらくならない最低限」を守るための既定です。

| チェック | ツール |
|----------|--------|
| secret 検出 | gitleaks（常時有効） |
| smoke test | app / plugin manifest / guard 最小確認 |
| lint | ruff |
| Markdown lint | textlint（必要時のみ） |

詳細な対処は [トラブルシューティング](docs/TROUBLESHOOTING.md) にまとめます。

## 📜 ライセンス

MIT License です。詳細は [LICENSE](LICENSE) を参照してください。
