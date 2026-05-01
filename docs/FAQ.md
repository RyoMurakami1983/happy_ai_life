# FAQ

## インストールとセットアップ

### Q: 先に Copilot CLI が必要ですか？

**A:** はい。skills と agents を動かす本体が Copilot CLI です。  
https://github.com/github/copilot-cli

**macOS (Homebrew):**

```bash
brew install github/gh-copilot/gh-copilot
```

**Windows (Winget):**

```powershell
winget install GitHub.Copilot
```

### Q: どの導入方法を選べばよいですか？

**A:** 用途で選んでください。

| 導入方法 | 向いている場面 | 手軽さ |
|----------|----------------|--------|
| Marketplace Plugin | skills を使いたいだけ | いちばん簡単 |
| ローカル開発 | この repo を改善したい | 中くらい |
| repo 初期導入 | チーム repo に入れたい | 中くらい |

詳しくは [はじめに](GETTING_STARTED.md) を参照してください。

### Q: 複数の導入方法を併用できますか？

**A:** できます。公開利用は marketplace、個人調整は home sync、チーム共有は repo bootstrap という併用ができます。

## 配布方法

### Q: marketplace install と direct install の違いは何ですか？

**A:**  

- **marketplace install**: 現在の主導線です。`copilot plugin install` で更新します。
- **direct install**: 古い導線です。新しい Copilot CLI では非推奨です。

新規導入では marketplace を使ってください。

### Q: direct install と marketplace install を同時に使えますか？

**A:** 非推奨です。重複表示されやすいため、先に旧版を外してください。

```powershell
copilot plugin uninstall happy-ai-life
copilot plugin install happy-core@happy-ai-life-marketplace
```

## Home Sync と Repo Bootstrap の違い

### Q: home sync とは何ですか？

**A:** `home-template/` の内容を `$HOME/.copilot/` に同期する仕組みです。信頼済みの個人環境を再現するときに使います。

使う場面:

- 作者環境を再現したい
- この repo に貢献したい
- 個人用に skill を調整したい

詳しくは [Home Sync（個人環境同期）](HOME_SYNC.md) を参照してください。

### Q: repo bootstrap とは何ですか？

**A:** 対象 repo に instructions、hooks、品質ゲートを入れる仕組みです。変更は repo に残るため、チーム全体に効きます。

使う場面:

- チーム repo に Copilot guidance を入れたい
- secret 検出などの安全弁を揃えたい
- Git hooks を共通化したい

詳しくは [Repo Bootstrap（repo 初期導入）](REPO_BOOTSTRAP.md) を参照してください。

### Q: どう使い分けますか？

| 場面 | 使うもの |
|------|----------|
| 個人環境を整える | Home Sync |
| この repo に貢献する | Home Sync |
| チーム repo に導入する | Repo Bootstrap |
| 個人で skill を調整する | Home Sync |
| チームの標準運用を揃える | Repo Bootstrap |

## Context7

### Q: Context7 は同梱されていますか？

**A:** いいえ。Upstash の外部 plugin です。この repo には含めていません。

### Q: Context7 を入れるには？

**A:** 必要なら別 plugin として入れます。

```powershell
copilot plugin marketplace add upstash/context7
copilot plugin install context7-plugin@context7-marketplace
```

API key は https://context7.com で取得してください。

## カスタマイズ

### Q: custom skill は作れますか？

**A:** 作れます。[作成ガイド](AUTHORING.md) を参照してください。

### Q: Doc 作成専用の skill は必要ですか？

**A:** いまは必須ではありません。README や `docs/*.md` の小さな更新は通常の編集で十分です。

custom skill / agent / repository instructions 自体を新規作成・改善・検証したいときは `copilot-authoring` を使ってください。  
文書構成そのものを大きく見直すときだけ、専用 skill を追加する価値があります。

### Q: project 固有の instructions はどう入れますか？

**A:** bootstrap 後に `.github/copilot-instructions.md` を編集します。必要なら `.github/instructions/<language>.instructions.md` も追加します。

### Q: custom skill を他の人と共有できますか？

**A:** できます。plugin として配布できる形にしてください。詳しくは [作成ガイド](AUTHORING.md) を参照してください。

## トラブル対応

### Q: `/skill list` に skill が出ません

**A:** 次を確認してください。

1. `copilot plugin list`
2. `copilot skill list <plugin-name>`
3. home sync を使っているなら `uv run app.py home --dry-run`

### Q: Git hooks が commit を止めます。回避してよいですか？

**A:** 基本は回避しないでください。secret 流出防止のためです。まず検出された内容を直してください。

どうしても一時回避が必要なら:

```powershell
git commit --no-verify
```

ただし、その後で手動確認してください。

```powershell
gitleaks detect --source . --verbose
```

## サポート

### Q: issue はどこに出せますか？

**A:** 次に起票してください。  
https://github.com/RyoMurakami1983/happy_ai_life/issues

あるとよい情報:

- 再現手順
- 期待した動作
- 実際の動作
- OS とバージョン

### Q: どう貢献できますか？

**A:** [開発ガイド](DEVELOPMENT.md) を参照してください。

### Q: 更新を追うには？

**A:** repo を watch してください。新しい skill や改善が反映されます。

## 関連

- [はじめに](GETTING_STARTED.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [開発ガイド](DEVELOPMENT.md)
