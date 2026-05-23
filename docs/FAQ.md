# FAQ

## まず何を入れればよいですか？

通常利用なら plugin install だけで十分です。

```powershell
copilot plugin marketplace add RyoMurakami1983/happy_ai_life
copilot plugin install happy-core@happy-ai-life-marketplace
copilot plugin install happy-coding@happy-ai-life-marketplace
```

## Home Sync は必要ですか？

この repo 自体を改善する人向けです。通常利用だけなら不要です。

## Team Repo Setup は必要ですか？

別 repo に HappyDefault の guidance、Git hooks、品質ゲートを入れたい場合だけ使います。日常導線ではありません。

## skill が多くて迷ったら何を使えばよいですか？

まずは [README](../README.md) の「迷ったらこれだけ」を見てください。詳細は [はじめに](GETTING_STARTED.md) の 3 パスで選べます。

- 通常利用なら **パス 1: 通常利用**
- この repo を改善するなら **パス 2: この repo を改善する**
- 既存 repo に導入するなら **パス 3: 既存 repo に導入する**

skill 名で探したい場合だけ次を使ってください。

```text
/skill list happy-core
/skill list happy-coding
```

## Git hooks が commit を止めます。回避してよいですか？

原則として回避しません。`git commit --no-verify` や `git push --no-verify` は使わないでください。

secret 検出なら内容を修正します。誤検出なら `.gitleaks.toml` の allowlist を最小範囲で調整し、理由が分かる変更として扱います。

## skill / agent / instructions は作れますか？

作れます。まず [作成ガイド](AUTHORING.md) の最小構成に合わせて、小さく追加してください。

## 困ったときは？

[トラブルシューティング](TROUBLESHOOTING.md) を参照してください。
