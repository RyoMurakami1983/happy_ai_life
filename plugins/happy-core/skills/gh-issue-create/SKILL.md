---
name: gh-issue-create
description: >
  スコープ外や後続対応を、実行可能な GitHub Issue として記録・具体化する。Use when: PR レビュー中に見つけた別件を切り出したいとき、サポート依頼を開発タスクに変えたいとき、曖昧な依頼を backlog 化したいとき。
---
# Issueインテーク

スコープ外のバグや改善を、再現可能で追跡可能なGitHub Issueとして記録し、曖昧なIssueは「行動可能」な形に具体化します。

## こんなときに使う
以下の状況で活用してください：
- Pull Request (PR)レビュー中に見つけたバグを切り分けたい
- 今すぐ対応しない修正をスプリント後に回したい
- Issueのタイトル、ラベル、優先度を標準化したい
- **内容が曖昧で何を直したいのか分からないIssueを、タイトル/本文から具体化したい**
- 断続的な障害の再現手順を記録したい
- サポート依頼を開発タスクとして追跡したい
- フォローアップ作業を別担当に引き渡したい

## 関連スキル

- **`git-commit`** - コミット運用と実践
- **`gh-pr-create`** - PR運用とマージ方針
- **`skill`** - 変更管理と履歴・ドキュメント品質の整理
- **`knowledge-capture`** - 公開リポジトリ向けコンテンツの匿名化ゲート
- **`references/origin.md`** - vertical-slice Issue 分割の出典メモ

---

## 依存関係

- GitHubアカウント（リポジトリ権限）
- GitHub CLI (gh)（CLI運用時・任意）
- チームのラベル/優先度規約

---

## コア原則

1. **行動可能性** - すべてのIssueに明確な次のステップを含める（基礎と型）
2. **スコープ分離** - 今の作業をブロックせずに後続作業を追跡する（ニュートラル）
3. **トレーサビリティ** - IssueをPRと証拠に紐付ける（成長の複利）
4. **一貫性** - 標準ラベル・優先度・テンプレートを使う（温故知新）
5. **検証可能性** - 挙動変更や運用変更を含むIssueには、観測可能で反証可能な受け入れ条件を置く
6. **低摩擦** - 素早く記録して忘れない（継続は力）

---

## ワークフロー: 先送りした作業をIssueとして記録する

### Step 1: 今直すかIssue化するか判断

インラインで修正するか先送りするかを判断します。影響度・工数・スコープ関連性に基づくシンプルな判断マトリクスを使います。スコープ外または30分のタイムボックスを超える場合はIssue化します。

```text
# ✅ CORRECT - スコープ外はIssue化
Issue: "🟡 CSV import: UTF-8 BOM を受け付けない"
Scope: 現PRでは不要
Action: Issueを作成して続行

# ❌ WRONG - TODOで埋める
// TODO: fix later
```

**いつ**: PR中にスコープクリープを発見した場合、または修正が現リリースを遅延させるリスクがある場合。

### Step 1.5: 匿名化ゲートの適用（公開リポジトリ向け）

コンテンツを書く前に、投稿先リポジトリが**公開**かどうかを確認する。公開の場合は [`knowledge-capture` の匿名化チェックリスト](../../knowledge-capture/SKILL.md#%E5%8C%BF%E5%90%8D%E5%8C%96%E3%83%81%E3%82%A7%E3%83%83%E3%82%AF%E3%83%AA%E3%82%B9%E3%83%88)（AC-1〜AC-4）を適用する：

| チェック | Issueで確認すべき内容 |
|---------|---------------------|
| AC-1 | プロジェクト名・組織名・private repoの名前（例: `MyOrg/my-private-repo`）|
| AC-2 | 内部ID・データフォーマット・private codebase固有の関数名/クラス名 |
| AC-3 | 内部システムや顧客を特定するドメイン固有用語 |
| AC-4 | 実際の閾値・設定値・業務固有の数値 |

Issue本文を書く前に、固有の詳細を汎用表現に置き換える。

```markdown
# ❌ NG — private repoの固有名詞がそのまま
## 背景
optimizer_project の internal_function_name バグ修正時に実践。
参考: MyOrg/my-private-repo PR #3

# ✅ OK — 匿名化済み
## 背景
数値最適化ライブラリのバグ修正セッションで実践。
参考: (private repo / 社内PR)
```

**判断基準**: 投稿先リポジトリは公開か？ → Yes = 書く前に AC-1〜AC-4 を適用する。

> **Values**: ニュートラルな視点（固有知識を普遍化して公開する）

**いつ**: 社内プロジェクトの作業を参照するIssueを公開リポジトリに作成するたびに。

### Step 2: タイトルと本文を書く（または既存Issueを具体化する）

検索しやすいタイトルと、構造化された本文を書きます。曖昧Issueはここで「目的・範囲・受け入れ条件・DoD」が分かる形に書き直します。
このリポジトリでは、Issue のタイトルと本文は日本語を既定にします。認知しやすさを優先し、固有名詞・CLI コマンド・コード識別子・外部サービス名は必要に応じて英語のまま残します。

#### 推奨: タイトルの優先度マーカー（カラー丸）

トリアージで一目で分かるように、タイトル先頭にカラー丸を付けます。ラベルを正としつつ、可視性を上げるための補助として使います。

| マーカー | 意味 | 目安 |
|---------|------|------|
| 🔴 | 緊急 / P0 | 本番停止 |
| 🟡 | High / P1 | 重大影響 |
| 🟢 | Medium / P2 | 標準バグ/改善 |
| 🔵 | Low / P3 | 軽微/整理 |

例：
- `🟡 validate_skill.py: Workflow/Router向けのセクション抽出を堅牢化する`
- `🟢 gh-issue-create: Issueは日本語で起票する方針を明記する`

#### 本文テンプレ

#### 受け入れ条件と DoD の使い分け

- **Acceptance Criteria**: Issue が「期待した挙動や運用結果を満たした」と判断するための条件。実装詳細ではなく、外から観測できる結果を書く。
- **Definition of Done**: 実装や運用完了に伴う付帯作業。ドキュメント更新、関連リンク、運用手順更新などを置く。
- **必須ルール**: **挙動変更や運用変更を含むIssueでは `## Acceptance Criteria` を必須**にする。純粋な文言修正や軽微な docs-only Issue だけは DoD のみでもよい。

#### 推奨: vertical slice でIssueを切る

機能Issueは、層ではなくユーザー行動や受け入れ条件で切ります。最初のIssueは tracer bullet として、UI / API / domain / persistence / test など必要な経路を薄く縦断できる粒度にします。

| 分割 | 例 | 判断 |
|------|----|------|
| ✅ vertical slice | 「CSVを1件アップロードし、成功結果が画面に表示される」 | 受け入れ条件でcloseできる |
| ❌ horizontal slice | 「DB schemaだけ作る」「UIだけ作る」 | 単体では価値と完了条件が曖昧 |

Issue本文には、必要なら次を分けて書きます。

- **HITL**: 人間判断や仕様確認が必要な作業
- **AFK**: 受け入れ条件が明確で、エージェントに任せやすい作業
- **Non-goals**: 今回の slice ではやらない層・ケース

#### 厳密な Acceptance Criteria のチェックリスト

1. 1項目につき1つの結果だけを書く
2. 実装方法ではなく観測可能な結果を書く
3. 可能なら条件と結果を対にする（例: `When ... , then ...`）
4. 「分かったらOK」のような主観表現を避ける
5. スコープ外のものは `Non-goals` か本文で明示する
6. close 時に満たした / 満たしていないを第三者が判定できるようにする

#### 推奨テンプレ

```markdown
Title: "🟢 gh-issue-create: 受け入れ条件の書き方を明記する"

## 背景
Issue を具体化しても、close の判断が人によって揺れるケースがある。

## 問題
DoD だけでは「何を満たせば受け入れか」が曖昧で、実装やレビューの基準がぶれやすい。

## 提案
`gh-issue-create` に、挙動変更や運用変更を含むIssueでは Acceptance Criteria を必須にするルールを追記する。

## Acceptance Criteria
- [ ] 挙動変更や運用変更を含むIssueでは `## Acceptance Criteria` セクションが使われる
- [ ] 受け入れ条件は、第三者が満たしたか判定できる観測可能な結果で書かれる
- [ ] DoD と Acceptance Criteria の違いが、例つきで説明されている

## Definition of Done
- [ ] `gh-issue-create` のテンプレと例が更新されている
- [ ] docs-only Issue を例外扱いにする条件が分かる
```

**注意（Markdownの罠）**: 本文内で `<path>` のような表記はHTMLタグ扱いで消える場合があります。`PATH` / `FILE` のようなプレースホルダにするか、フェンス付きコードブロックを使ってください。

**いつ**: 新規Issue作成時、または「内容が分からないIssue」を具体化するとき。

### Step 3: ラベルと優先度を付与

バックログをソート可能にするため、種別・優先度・領域のラベルを付与します。**まずはその repo に実在するラベルを使う**ことを優先し、優先度ラベルが未整備の repo ではタイトル先頭のカラー丸で補います。

| 優先度 | 意味 | SLA |
|--------|------|-----|
| P0 | 本番停止 | 当日 |
| P1 | 重大影響 | 1–3日 |
| P2 | 標準バグ | 1–2スプリント |
| P3 | 軽微/整理 | バックログ |

```yaml
# ✅ CORRECT - repo にあるラベルを使う
labels: [enhancement]

# ✅ ALSO OK - custom labels がある repo
labels: [t/bug, p/high, a/import]

# ❌ WRONG
labels: []
```

**いつ**: トリアージミーティング前、または別メンバーへの引き渡し時。

### Step 4: 再現手順と証拠を追加

番号付きの再現手順、期待結果と実際の結果、裏付け証拠（ログ、スクリーンショット、リクエストID）を含めます。次の担当者がフォローアップの質問なしで問題を再現できるようにします。

```markdown
## Steps to Reproduce
1. Upload CSV with UTF-8 BOM
2. Click Import
3. Observe error in UI

## Expected
Import succeeds

## Actual
"Invalid encoding" error

## Evidence
Log: 2026-02-12T12:03:11Z ERROR import failed (BOM detected)
```

**いつ**: バグの場合は常に。機能の場合はユーザーシナリオのコンテキストを代わりに含める。

### Step 5: CLIでIssueを作成/更新（推奨）

`gh issue create` で新規作成、`gh issue edit` で既存Issueの具体化（title/body整備）を行います。

```bash
# 新規作成
gh issue create \
  --title "🟢 gh-issue-create: 受け入れ条件の書き方を明記する" \
  --body-file issue.md \
  --label enhancement \
  --assignee @me

# 更新（具体化）
gh issue edit 123 --title "🟢 Windows: UTF-8 入出力の標準化を行う" --body-file issue.md
```

#### Windows / PowerShell: 最も安全な body-file 手順（UTF-8）

PowerShellで `--body` に長文を直接渡すと、クォート崩れやハングの原因になりがちです。UTF-8でファイルを書き出して `--body-file` で渡してください。

```powershell
$bodyLines = @(
  '## 背景',
  '- close 判断が人によって揺れる Issue があった',
  '',
  '## Acceptance Criteria',
  '- [ ] 第三者が満たしたか判定できる条件で書かれている',
  '',
  '## Definition of Done (DoD)',
  '- [ ] ...'
)
$bodyFile = Join-Path $env:TEMP 'issue_body.md'
Set-Content -Path $bodyFile -Value $bodyLines -Encoding utf8

gh issue edit 123 --title '🟢 ...' --body-file $bodyFile
Remove-Item -LiteralPath $bodyFile -Force
```

**いつ**: ターミナルで作業中で、再現性と安全性を重視する場合。

### Step 6: Web UIでIssueを作成

ドラッグ＆ドロップのスクリーンショット、リッチMarkdownプレビュー、テンプレート選択が必要な場合はGitHub Web UIを使います。

```text
1. リポジトリ → Issues → New issue を開く
2. テンプレートを選択（例: Bug Report）
3. 必須項目を入力し、スクリーンショットを添付
4. ラベル、マイルストーン、担当者を追加
5. 送信
```

**いつ**: 埋め込み画像、複雑なフォーマット、またはブラウザからのトリアージが必要な場合。

### Step 7: IssueをPRにリンク

PR説明文にクローズキーワードを使ってIssueを参照し、マージ時に自動クローズさせます。

```markdown
## Related
Closes #123
Refs #130
```

クロスリポジトリ参照には完全な `owner/repo#N` 構文を使います：

```markdown
Fixes owner/repo#123
```

**いつ**: 追跡対象のIssueを解決または関連するすべてのPR。

---

## ベストプラクティス

- **「分からないIssue」を放置しない**：背景→目的→スコープ→Acceptance Criteria→DoD に整形して具体化する
- このリポジトリでは、日本語タイトル・日本語本文を既定にする
- ただし固有名詞・CLI コマンド・コード識別子・外部サービス名は、認知しやすさを優先して英語併記または英語のままでもよい
- タイトルの優先度マーカー（🔴🟡🟢🔵）をチームで統一する
- タイトルでは `標準化する`、`明記する`、`棚卸しする` のような明示的な日本語の動詞を使う
- 1 Issue = 1 問題に絞る
- 挙動変更や運用変更を含むIssueでは `## Acceptance Criteria` を省略しない
- Acceptance Criteria には実装方法を書かず、外から見える結果を書く
- トリアージ前に影響度と優先度を付ける
- 可能な限り再現手順か証拠を記載
- `--body-file` を基本にする（1行を超える本文は特に）

---

## よくある落とし穴

- "Bug" や "Fix later" のような曖昧なタイトル
- 断続的障害で再現手順を省略する
- 1つのIssueに複数の問題を混在させる
- 受け入れ条件が DoD に埋もれていて、close 判定の基準が読めない
- Acceptance Criteria に「実装する」「調査する」だけを書いてしまう
- PowerShellで `gh issue edit --body ...` に長文を直接渡す
- `<PATH>` のような表記が本文から消える（HTMLタグ扱い）
- リポジトリ内で英語起票と日本語起票が混在し、後から言語統一の手戻りが発生する

Fix: 標準テンプレートを使い、スコープ別にIssueを分割する。
Fix: Acceptance Criteria と DoD を分けて書く。
Fix: 再現手順か証拠リンクを必ず追加する。
Fix: UTF-8の `--body-file` 経由で編集する。

---

## アンチパターン

- TODOコメントでIssueを作らない
- 明確な次のアクションがないIssueを作る
- close 条件が曖昧なまま「実装方針メモ」だけでIssueを立てる
- 解決内容を記録せずIssueを閉じる

---

## FAQ

**Q: 今直すかIssue化するか、いつ判断すべき？**
A: 修正がスコープ外、またはタイムボックスを超える場合はIssue化する。

**Q: 既存Issueが曖昧で分からないときは？**
A: コメントで済ませず、title/bodyを具体化（背景・目的・Acceptance Criteria・DoD）して「次の人が動ける」状態にする。

**Q: Acceptance Criteria と DoD は何が違う？**
A: Acceptance Criteria は「何を満たせば受け入れか」、DoD は「完了時に揃っている付帯作業」です。挙動変更や運用変更を含むIssueでは両方を書く前提にします。

**Q: このリポジトリのIssueは日本語と英語のどちらで書くべき？**
A: 既定は日本語。固有名詞・CLI コマンド・コード識別子・外部サービス名は、認知しやすさを優先して英語のまま使ってよい。

**Q: 最低限必要なラベルは？**
A: まず repo に存在するラベルを1つ以上付ける。優先度ラベルが整備されている repo ではそれも付け、未整備ならタイトル先頭のカラー丸で補う。

---

## クイックリファレンス

| Step | アクション | 結果 |
|------|------------|------|
| 1 | 今直すかIssue化か判断 | 判断を記録 |
| 1.5 | 匿名化ゲートの適用（公開リポジトリ） | Issue内に固有データなし |
| 2 | タイトル/本文を作成（🔴🟡🟢🔵） | AC 付きで行動可能なIssue |
| 3 | repo にあるラベルを付与 | ソート可能なバックログ |
| 4 | 再現手順と証拠を追加 | 再現可能なレポート |
| 5 | CLIで作成/更新（`--body-file`） | 高速で安全 |
| 6 | Web UIで作成 | リッチフォーマット |
| 7 | PRにリンク | マージで自動クローズ |

---
```bash
# CLI で新規作成
gh issue create --title "🟢 改善: ..." --body-file issue.md --label enhancement

# CLI で更新
gh issue edit 123 --title "🟢 〜を明記する" --body-file issue.md
```

---

## Resources

- [About issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues)
- [Closing issues with keywords](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)
- [GitHub CLI issue create](https://cli.github.com/manual/gh_issue_create)
- [GitHub CLI issue edit](https://cli.github.com/manual/gh_issue_edit)

---
