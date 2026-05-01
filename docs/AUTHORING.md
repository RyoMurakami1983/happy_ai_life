# 作成ガイド

この文書は Copilot CLI 向けの skill、agent、instructions を作るときの入口です。

## まず用語を整理

### skill

skill は再利用できる単機能の入口です。

- **責務**: 1 つの作業をうまく進める
- **配布**: plugin にまとめる
- **呼び出し**: `/skill run <skill-name>`
- **例**: `gh-pr-create`、`sdd`、`furikaeri`

**向いている場面:** 繰り返し使う手順を他の人にも再利用してほしいとき。

### agent

agent は複数手順をまたいで動く実行者です。

- **責務**: 複数段の判断や実行を進める
- **呼び出し**: background / sync の task
- **特徴**: 文脈を持ちながら進められる
- **例**: `explore`、`code-review`、`tdd-coder`

**向いている場面:** 1 回の skill では収まらない作業を任せたいとき。

### instructions

instructions は Copilot へ常時渡す guidance です。

- **repo 単位**: `.github/copilot-instructions.md`
- **path 単位**: `.github/instructions/<language>.instructions.md`
- **個人環境**: `$HOME/.copilot/config.json`

**向いている場面:** 命名、境界、文体、運用などの常時ルールを固定したいとき。

## 作成の流れ

### 1. 設計

まず `/design-workshop` で整理します。

```powershell
copilot /design-workshop
```

確認したいこと:

- 何を解決したいか
- skill にするか agent にするか
- 既存資産を再利用できるか

### 2. 計画

PLAN mode で作業を分解します。

```powershell
copilot /plan
```

最低限、次を固定します。

- 問題
- アプローチ
- 成功条件
- 確認手段

### 3. 実装

複雑な処理なら specialist を使います。

```powershell
copilot /skill run tdd-coder
```

### 4. 検証

`copilot-authoring` を使って整合を見ます。

```powershell
copilot /skill run copilot-authoring
```

主に次を確認します。

- `SKILL.md` の構造
- 設定の整合
- README や関連 docs との導線

### 5. 提出

```powershell
git add .
git commit -m "feat: 新しい skill を追加"
gh pr create
```

## 作るときの基本

### skill

- 1 skill 1 役割に寄せる
- `こんなときに使う` を明確に書く
- `_eval/tests/` に確認材料を置く
- 名前は短い kebab-case にする

### agent

- 広すぎる万能 agent を作らない
- 文脈量を意識する
- 失敗時の扱いを決める
- 判断の痕跡を残す

### instructions

- 誰向けの rule か明示する
- 抽象論より具体例を優先する
- 境界変更時は README や周辺 docs も揃える
- 長い手順は instructions に詰め込まず skill や docs に逃がす

## ひな形

### skill の例

```text
skills/your-skill/
├── SKILL.md
├── manifest.json
├── scripts/
│   └── main.py
├── _eval/
│   ├── scripts/
│   │   └── validator.py
│   └── tests/
│       └── test_*.py
```

### agent の例

```text
agents/your-agent/
├── AGENT.md
├── manifest.json
├── scripts/
│   └── main.py
├── requirements.txt
└── tests/
    └── test_*.py
```

## 関連

- [開発ガイド](DEVELOPMENT.md)
- [リファレンス](REFERENCE.md)
- [品質ゲート](QUALITY_GATES.md)
