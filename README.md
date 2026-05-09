# happy_ai_life

> 楽しく AI と続ける仕事・学習・コーディングの型を、いつでもどこでも再現できるようにする。

Copilot CLI の reusable skills、agents、repo bootstrap 資産を管理する母艦リポジトリです。  
背景は [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) を参照してください。

## 🚀 クイックスタート

### インストール

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

セットアップ後は [はじめに](docs/GETTING_STARTED.md) を参照してください。

## 📚 ドキュメント

| 目的 | ドキュメント |
|------|--------------|
| 導入手順をまとめて見る | [はじめに](docs/GETTING_STARTED.md) |
| 個人用のローカル環境を整える | [Home Sync（個人環境同期）](docs/HOME_SYNC.md) |
| 既存の repo に Copilot を入れる | [Repo Bootstrap（repo 初期導入）](docs/REPO_BOOTSTRAP.md) |
| GitHub 側の保護設定をそろえる | [Enterprise Security（企業向け保護設定）](docs/ENTERPRISE_SECURITY.md) |
| この repo の開発手順を見る | [開発ガイド](docs/DEVELOPMENT.md) |
| skill / agent / instructions を作る | [作成ガイド](docs/AUTHORING.md) |
| コマンド・skills・ADR 一覧を見る | [リファレンス](docs/REFERENCE.md) |
| よくある問題の解決方法を見る | [トラブルシューティング](docs/TROUBLESHOOTING.md) |
| よくある質問を見る | [FAQ](docs/FAQ.md) |
| 思想と価値観を知る | [開発思想](docs/PHILOSOPHY.md) |

## 🔧 この repo を変更するとき

この repo には Copilot CLI plugin、bootstrap script、品質確認用ツールが入っています。

1. **設計** — `/design-workshop` または design-workshop skill を使う
2. **計画** — PLAN mode で実装を分解する
3. **確認** — PR 前に品質チェックを流す

```powershell
uv run pytest -q
uv run ruff check .
uv run ty check .
```

詳しくは [開発ガイド](docs/DEVELOPMENT.md) を参照してください。

## ✅ 品質ゲート

この repo では PR ごとに GitHub Actions の品質チェックを実行します。

| チェック | ツール |
|----------|--------|
| secret 検出 | gitleaks（常時有効） |
| Markdown lint | textlint（必要時のみ） |

設定と対処方法は [品質ゲート](docs/QUALITY_GATES.md) を参照してください。

## 📜 ライセンス

MIT License です。詳細は [LICENSE](LICENSE) を参照してください。
