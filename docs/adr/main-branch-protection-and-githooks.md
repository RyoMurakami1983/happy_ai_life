# Main 保護を Branch Protection と Git hooks で多層化する

**日付**: 2026-04-01  
**ステータス**: 承認

---

## 背景

このリポジトリでは `main` への直接 commit / push を誤って実行しないための
仕組みが必要だった。ローカルの誤操作は hooks で早期に止められるが、
`--no-verify` や設定変更で回避できるため、ローカルだけでは「確実」と言えない。

一方で、GitHub の Branch Protection / Ruleset はサーバー側で
`main` への直接 push / merge を強制的に抑止できるため、最終的な保護点として必要になる。

## 判断

- **GitHub Branch Protection / Ruleset を必須の本丸**とする
- **repo-scoped Git hooks** を補助防御として追加する
- hooks の配布テンプレートは `repo-template/.githooks/` に置く
- 対象リポジトリでは `.githooks/` に同期し、`core.hooksPath` で有効化する
- この母艦リポジトリ自身では `repo-template/.githooks/` を `core.hooksPath` として参照できるようにする

## 根拠

- サーバー側保護だけが、直接 push を強制的に止められる
- ローカル hooks はユーザーの手元で即時に誤操作を防げる
- テンプレートと実装を分けることで、同期先リポジトリにも同じ保護を配布できる
- `.github/hooks/` は Copilot hooks の正本であり、Git client hooks とは役割を分けたほうが混乱しない

## トレードオフ

- **得るもの**
  - 誤 commit / 誤 push の早期防止
  - 配布可能なローカル保護
  - サーバー側の強制保護による確実性
- **失うもの**
  - 設定項目が増える
  - hooks 単独では完全防御にならない

## 運用

- `scripts/install-git-hooks.ps1` で hooks をインストールする
- `scripts/sync-to-repo.ps1` で target repo に `.githooks/` を配布する
- GitHub で `main` の Branch Protection / Ruleset を有効化する

## 状態

承認
