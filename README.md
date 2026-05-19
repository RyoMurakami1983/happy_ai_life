# happy_ai_life

> 楽しく AI と続ける仕事・学習・コーディングの型を、いつでもどこでも再現できるようにする。

Copilot CLI の reusable skills、agents、repo bootstrap 資産を管理する母艦リポジトリです。

## 🚀 クイックスタート

### インストール

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

日常利用は [はじめに](docs/GETTING_STARTED.md) だけ読めば始められます。

## 📚 ドキュメント

| 目的 | ドキュメント |
|------|--------------|
| 最短で使い始める | [はじめに](docs/GETTING_STARTED.md) |
| この repo を変更する | [開発ガイド](docs/DEVELOPMENT.md) |
| 確認方針を見る | [品質ゲート](docs/QUALITY_GATES.md) |
| skill / agent / instructions を作る | [作成ガイド](docs/AUTHORING.md) |
| よくある質問を見る | [FAQ](docs/FAQ.md) |
| 困ったとき | [トラブルシューティング](docs/TROUBLESHOOTING.md) |

## 🔧 この repo を変更するとき

この repo には Copilot CLI plugin、bootstrap script、品質確認用ツールが入っています。

1. **設計** — `/design-workshop` または design-workshop skill を使う
2. **計画** — PLAN mode で実装を分解する
3. **確認** — 変更範囲に合う focused check を流す

```powershell
uv run python -m pytest -q tests/test_app_smoke.py tests/test_plugin_manifest.py tests/test_secret_guard_minimal.py
uv run ruff check .
```

詳しくは [開発ガイド](docs/DEVELOPMENT.md) を参照してください。

## ✅ 品質ゲート

この repo では `HappyDefault` を既定にし、PR は smoke test と ruff を優先します。full quality は必要なときに manual workflow で実行します。

| チェック | ツール |
|----------|--------|
| secret 検出 | gitleaks（常時有効） |
| smoke test | app / plugin manifest / guard 最小確認 |
| lint | ruff |
| Markdown lint | textlint（必要時のみ） |

詳細な対処は [トラブルシューティング](docs/TROUBLESHOOTING.md) にまとめます。

## 📜 ライセンス

MIT License です。詳細は [LICENSE](LICENSE) を参照してください。
