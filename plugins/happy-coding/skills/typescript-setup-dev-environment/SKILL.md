---
name: typescript-setup-dev-environment
description: >
  Node.js / npm を基準に、再現可能な TypeScript 開発環境を整える。
  こんなときに使う: 新規 TypeScript プロジェクトを strict 前提で始めたいとき、
  lint / format / test を標準化したいとき、ESLint / Prettier / Jest / VS Code の
  足並みをそろえたいとき。
metadata:
  author: RyoMurakami1983
  tags: [typescript, nodejs, npm, eslint, prettier, jest, vscode]
  invocable: false
---

# TypeScript 開発環境を整える

TypeScript の再現性は、`tsc` だけでなく npm scripts・lint・format・test・editor 設定まで
まとめて固定してはじめて効きます。この skill は hot path を短く保ち、詳細な設定例は
`references/` に逃がす router 風の実行ガイドです。

## こんなときに使う

- 新しい TypeScript プロジェクトを strict 前提で始めたいとき
- Node.js / npm を基準に team 共通の開発手順をそろえたいとき
- ESLint と Prettier の役割分担を整理したいとき
- Jest と npm scripts を追加して CI とローカルの差分を減らしたいとき
- VS Code 保存時の format / lint 挙動をそろえたいとき

## 関連スキル

- `typescript-tauri-setup` — この土台に Tauri を重ねたいとき
- `git-initial-setup` — 最初の commit 前に branch 保護を整えたいとき
- `git-commit` — 環境変更を原子的に commit したいとき
- `gh-pr-create` — セットアップ変更を PR で流したいとき

## 判断表

| やりたいこと | まずやること | 詳細 |
| --- | --- | --- |
| 新規プロジェクトを始める | `npm init -y` と `npm i -D typescript` | `references/starter-configs.md` |
| lint / format を整える | ESLint + Prettier を devDependencies に追加 | `references/starter-configs.md#eslint--prettier` |
| test を追加する | Jest + ts-jest を追加し npm scripts をそろえる | `references/starter-configs.md#jest` |
| VS Code もそろえる | `.vscode/settings.json` と拡張推奨を置く | `references/starter-configs.md#vs-code` |
| CI と同じ再現性を確認する | `npm ci` → `format` → `lint` → `build` → `test` | `references/starter-configs.md#verification` |

## ワークフロー: TypeScript 開発環境を整える

### ステップ 1: Node.js と npm を固定する

Node.js LTS と npm を先にそろえます。なぜなら、ここがズレると同じ `package-lock.json` を
持っていても依存解決やスクリプト挙動が微妙に変わるためです。

```powershell
node --version
npm --version
```

新しい開発端末なら Node.js LTS を入れてから進めます。npm はグローバル導入を増やさず、
プロジェクトローカルの依存と npm scripts を入口にします。

### ステップ 2: プロジェクトの土台を作る

最小構成は `package.json`・`package-lock.json`・`tsconfig.json` です。C# の `.csproj` や
Python の `pyproject.toml` と同じく、依存と実行入口をここに寄せます。

```powershell
npm init -y
npm install --save-dev typescript
```

- `tsconfig.json` は `strict: true` を起点にする
- ES Modules を使うなら相対 import に `.js` 拡張子を付ける
- `src/` と `dist/` を分け、型チェックと出力先を明確にする

設定例は `references/starter-configs.md#typescript` を参照します。

### ステップ 3: 品質ゲートを追加する

TypeScript 単体では format・lint・test まで面倒を見ません。そこで ESLint / Prettier / Jest を
足し、毎日の入口を npm scripts に統一します。なぜこの順序かというと、editor と CI が同じ
コマンド列を共有でき、レビュー前に壊れやすい境界を早く見つけられるからです。

- ESLint: 静的解析と未使用変数検出
- Prettier: 書式の自動整形
- Jest: テスト実行と最低限の回帰確認
- npm scripts: `build` / `lint` / `format` / `test` の共通入口

具体的な依存追加と設定ファイルは `references/starter-configs.md#quality-gates` を参照します。

### ステップ 4: エディタと再現性を閉じる

ローカルでは通るのに CI で壊れる、という差分を減らすには editor 設定と lock file 運用まで
閉じる必要があります。

- VS Code では format on save と ESLint fix を明示する
- `package-lock.json` を commit して依存状態を固定する
- CI や fresh clone では `npm install` ではなく `npm ci` を使う
- 最後に `format → lint → build → test` を通す

検証手順は `references/starter-configs.md#verification` を参照します。

## 注意点

- **グローバル install を増やさない**: `npm install -g typescript` のような運用は端末ごとの drift を生みます。
- **`strict` を後回しにしない**: 後から厳格化すると既存コード全体の修正コストが跳ね上がります。
- **ESM の `.js` 拡張子を忘れない**: `.ts` のまま import しても、実行時には `.js` を解決します。
- **CI で `npm install` を使わない**: lock file を使った再現性確認が弱くなります。
- **`package-lock.json` を無視しない**: 再現可能なセットアップの根拠なので version control に含めます。

## クイックリファレンス

```powershell
npm init -y
npm install --save-dev typescript eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
npm install --save-dev jest ts-jest @types/jest
npm ci
npm run format
npm run lint
npm run build
npm run test
```

## 参照資料

- `references/starter-configs.md` — `tsconfig.json`、ESLint、Prettier、Jest、VS Code の設定例
- [Node.js documentation](https://nodejs.org/docs/latest/api/)
- [TypeScript documentation](https://www.typescriptlang.org/docs/)
- [ESLint documentation](https://eslint.org/docs/latest/)
- [Prettier documentation](https://prettier.io/docs/)
- [Jest documentation](https://jestjs.io/docs/getting-started)
