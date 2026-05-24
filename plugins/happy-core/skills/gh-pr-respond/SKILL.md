---
name: gh-pr-respond
description: >
  PR レビューコメントを blocking / non-blocking / reply-only に分類し、
  必要な修正だけを外科的に実装して、返信、再レビュー依頼、
  人間へのマージ判断引き継ぎまで進める。Use when: PR に review signal が届き、
  修正・棄却・保留を構造化して扱いたいとき。
---
# GitHub PR Review Response

PR レビュー対応を、**修正すべきもの**と**返信で閉じるもの**に分けて扱う workflow です。  
この skill は「全部直す」ためではなく、**正しさ・安全性・公開品質に効くものだけを直し、残りは理由付きで丁寧に閉じる**ために使います。

標準ルートは `implementation -> gh-pr-create -> review signal -> gh-pr-respond -> 人間のマージ判断` です。  
この skill は、レビュー待機中ではなく**実際に対応が必要なシグナルが来た時点**で始めます。

## こんなときに使う

- PR にレビューコメントが付き、修正と返信を整理して進めたいとき
- バグ指摘と細かな改善提案を分け、blocking だけ先に直したいとき
- nitpick が増えてきたレビューを、reply-first で穏当に閉じたいとき
- スコープ外提案を Issue 化すべきか、返信のみで止めるべきか判断したいとき
- 新しいコミットがあるときだけ再レビュー依頼し、無駄な ping を避けたいとき
- 最後は人間のマージ判断へ安全に引き渡したいとき

> **スコープ**: この skill はレビューコメントのトリアージ、必要な修正、返信、必要時のみの再レビュー依頼までを扱います。マージ判断は人間が行います。

## レビュー待機戦略

PR が open なだけでは開始しません。**新しい review signal が来たときだけ**この workflow に入ります。

| シグナル | この skill に入る？ | アクション |
| --- | --- | --- |
| 新しいレビューが送信された | はい | Step 1 を 1 回開始 |
| 自分に review request が来た | はい | Step 1 を 1 回開始 |
| ユーザーが新規レビュー到着を共有した | はい | 確認して Step 1 を開始 |
| PR は open だが変化なし | いいえ | 待機継続 |
| CI ステータスだけ変わった | 場合による | 本当にレビュー対応が必要か確認 |

低消費で待つルール:

- 手動ポーリングより、通知・ユーザー共有・イベントシグナルを優先する
- 手動確認が必要でも、自然な区切りでまとめて 1 回だけ見る
- 対応すべき新しいシグナルがなければ確認を止める

## 関連スキル

- **`gh-pr-create`** — PR 作成とレビュー待機の上流
- **`git-commit`** — 原子的コミットと Conventional Commits
- **`gh-issue-create`** — 再利用価値がある deferred 項目だけ Issue 化する

---

## 依存関係

- Git 2.30+
- GitHub CLI (`gh`) — `gh auth status` で事前確認
- push 権限を持つオープン PR
- 対応すべきレビューコメント、または review request

---

## コア原則

1. **blocking にはコードで対応する** — バグ、セキュリティ、明確なロジック破綻、受け入れ条件や公開品質を満たさない不足は、マージ前に修正する
2. **non-blocking は reply-first** — 改善提案やスコープ外の不足は、まず返信で棄却・保留・採用判断を行い、修正は既定にしない
3. **すべてのコメントに返信する** — 修正しない場合も、無視せず理由を添えて閉じる
4. **asset-sensitive に判断する** — 公開配布物、安全境界、reviewer-facing policy は厳しめに扱い、試作や局所 docs は緩めに扱う
5. **Issue は再利用価値があるときだけ作る** — 横断価値、再発防止、共有価値がある deferred 項目だけ backlog 化する
6. **graceful stop を許可する** — 非ブロッカーな細部レビューだけが残ったら、返信のみで締めて人間のマージ判断へ渡せる
7. **外科的で追跡可能に進める** — 今回のコメントに直接効く最小差分へ絞り、返信で変更理由をたどれるようにする

---

## 判断テーブル

まず各コメントを **blocking / non-blocking / reply-only** に分類します。

| コメント種類 | 既定分類 | 既定アクション | 優先度 | 例 |
| --- | --- | --- | --- | --- |
| バグ / セキュリティ | blocking | マージ前に必ず修正 | 最重要 | 「SQL インジェクションの脆弱性がある」 |
| ロジックエラー | blocking | マージ前に必ず修正 | 最重要 | 「この条件が反転している」 |
| 機能不足（受け入れ条件・安全性・公開品質に直結） | blocking | マージ前に修正 | 高 | 「この skill だと再レビュー不要条件が欠けている」 |
| 機能不足（今回のスコープ外、後回し可能） | non-blocking | reply-first。必要時のみ Issue | 中 | 「今後は分析サマリーを自動投稿したい」 |
| 改善提案 | non-blocking | reply-first。差分に直接効き Happy を上げるときだけ修正 | 中 | 「表を 1 つ追加すると判断しやすい」 |
| スタイル / フォーマット | reply-only | 理由付き返信。チーム合意がある場合だけ修正 | 低 | 「言い回しをもう少し柔らかく」 |
| 質問 / 確認 | reply-only | 説明を返信 | 低 | 「なぜこの分類にしたの？」 |

### 機能不足の `scope_sensitive` ルール

機能不足は一律に扱いません。次のどれかに当てはまるときだけ blocking です。

- 受け入れ条件を満たさない
- 正しさ / 安全性 / trust boundary を壊す
- 公開配布物としての基本品質を欠く

それ以外の不足は **reply-first** を既定にし、必要なら Issue を検討します。

### 返信の型

| disposition | 使う場面 | やること |
| --- | --- | --- |
| `fix` | blocking、または価値が明確な non-blocking | 実装して返信 |
| `reply-only` | 質問、確認、軽微なスタイル指摘 | 理由付き返信のみ |
| `reject-with-reply` | 今回は採らない提案 | 採らない理由を返信 |
| `defer-with-issue` | 今回は採らないが再利用価値がある | Issue を作成して返信 |

## asset-sensitive テーブル

この表は、**コメントに対して修正するか返信で閉じるか**の判断に使います。  
**品質チェックの範囲**は Step 4 の focused checks / full quality gate ルールに従います。

| 対象資産 | 厳しさ | non-blocking コメントの既定 |
| --- | --- | --- |
| 公開配布物、safety guard、reviewer-facing skill / policy | 高 | 公開品質や誤用防止に直接効くものは採用しやすい |
| 通常の共有 docs、共有 script、一般 skill | 中 | reply-first。差分に直接効くものだけ採用 |
| `works/`、試作、局所 docs、単発作業物 | 低 | reply-first。棄却や保留を選びやすい |

---

## 責務境界

| フェーズ | エージェントの責務 | 人間の責務 |
| --- | --- | --- |
| レビューシグナル受付 | 新規レビューを 1 回だけ確認し、コメントを分類する | そのシグナルで優先順位が変わるか判断する |
| 修正と返信 | blocking を直し、non-blocking は reply-first で閉じる | 返信内容がチーム期待に合うか判断する |
| Issue 化 | 再利用価値がある deferred 項目だけ Issue 化する | backlog として持つ価値があるか最終判断する |
| 再レビュー依頼 | 新しいコミットや実質的な更新があるときだけ依頼する | 追加レビュアーが必要か判断する |
| マージ判断 | 準備完了状況を要約して止まる | GitHub 上でマージ可否と時期を決める |

> **Values**: ニュートラル / 余白の設計

## ワークフロー: PR レビュー対応

### Step 1: レビューコメントを 2 軸で分類する

PR のコメントを、**コメント種類**と**対象資産の厳しさ**の 2 軸で整理します。

```bash
gh pr view --json reviews,reviewRequests --jq '.reviews'
gh pr view --json reviewThreads --jq '.reviewThreads[] | {path: .path, body: .comments[0].body, isResolved: .isResolved}'
```

```powershell
gh pr view --json reviews,reviewRequests --jq '.reviews'
```

分類メモの例:

```markdown
## レビューコメント分析
| # | ファイル | コメント種類 | 資産厳しさ | disposition | 理由 |
|---|---|---|---|---|---|
| 1 | src/auth.py | バグ | 高 | fix | マージ前に必須 |
| 2 | plugins/happy-core/.../SKILL.md | 改善提案 | 高 | fix | 誤用防止に直接効く |
| 3 | README.md | スタイル | 中 | reply-only | 表現差のみ |
| 4 | works/foo/SKILL.md | 機能不足 | 低 | reject-with-reply | 今回のスコープ外 |
```

> **Values**: 温故知新 / 基礎と型

### Step 2: 対応計画を作る

plan.md か会話メモで、**何を直すか**だけでなく**何を返信のみで閉じるか**も明示します。

```markdown
# PR レビュー対応計画

## fix
1. reviewer-facing policy の抜けを補う
2. 返信テンプレの誤誘導を直す

## reply-only
1. wording 提案には理由付きで返信する

## defer-with-issue
1. 他 skill にも効く横断改善だけ Issue 化する

## graceful stop 条件
- 残りが non-blocking / reply-only だけになったら返信で締める
- 新しいコミットがないなら再レビュー依頼は送らない
```

Issue を作るのは、**今回閉じても次回以降に価値が残るものだけ**です。  
「とりあえず backlog」にはしません。

> **Values**: 基礎と型 / 余白の設計

### Step 3: blocking と高価値の修正だけ実装する

blocking を先に直します。non-blocking は、**今回の差分に直接効き、長期的な Happy を上げるものだけ**を採用します。

```bash
git add path/to/file
git commit -m "fix: レビュー対応で blocking な抜けを補完

受け入れ条件に直結するレビューコメントへ対応。"
```

```powershell
git add path\to\file
git commit -m "fix: レビュー対応で blocking な抜けを補完"
```

✅ **推奨**: blocking と high-value fix に絞る  
✅ **推奨**: reply-first を既定にし、不要な実装反復を避ける  
❌ **非推奨**: 「ついでに直せる」改善を積み増す  
❌ **非推奨**: non-blocking を機械的に全部実装する

> **Values**: 基礎と型 / 成長の複利

### Step 4: 差分に合う checks を実行する

まず **focused checks** を実行します。  
reviewer-facing skill definition、workflow、hook、shared policy などに触れた場合は、repo guidance に従って **full quality gate** も追加します。

```bash
# 例: skill validator と manifest 確認
uv run python path/to/validator.py path/to/changed-skill --level L2
uv run pytest -q path/to/focused_test.py

# 必要な場合のみ full quality gate
uv run pytest -q
uv run ruff check .
uv run ty check .
```

```powershell
uv run python path\to\validator.py path\to\changed-skill --level L2
uv run python -m pytest -q path\to\focused_test.py
```

artifact-sensitive テーブルは**返信判断**のためのものです。  
check の範囲は、この Step 4 のルールで別に決めます。

> **Values**: 継続は力 / 基礎と型

### Step 5: 変更があるときだけコミットする

コードや文書を変えたときだけコミットします。返信だけで閉じる反復では、コミットを無理に作りません。

| コミットタイプ | 使用場面 |
| --- | --- |
| `fix:` | blocking なレビュー修正 |
| `refactor:` | 高価値の構造改善 |
| `docs:` | 文書や skill 本文の明確化 |
| `style:` | チーム合意済みの整形修正 |

> **Values**: 成長の複利 / 継続は力

### Step 6: push し、全コメントに返信する

修正したものは push し、**修正した / 採らない / 後回しにする**のどれでも必ず返信します。

```bash
git push origin HEAD
```

返信テンプレート:

```markdown
コミット `<ハッシュ>` で修正済み。

**変更内容**: <修正の簡潔な説明>
**このアプローチの理由**: <今回の差分に直接効き、受け入れ条件を満たすため>
```

```markdown
今回は返信のみで対応します。

**判断**: reject-with-reply
**理由**: <非 blocking であり、今回のスコープや Happy を考えると採用しないため>
```

```markdown
今回は本 PR では対応せず、フォローアップ Issue に切り出します。

**判断**: defer-with-issue
**理由**: <横断価値 / 再発防止価値があるため>
**Issue**: <リンク>
```

✅ **推奨**: 採らない理由を明示する  
✅ **推奨**: 複数行やバッククォートを含む本文は `--body-file` を使う  
❌ **非推奨**: 「修正済み」「見送りました」だけで終える  
❌ **非推奨**: Issue を作らない deferred 項目を無返信で流す

> **Values**: ニュートラル / 成長の複利

### Step 7: 新しい更新があるときだけ再レビューを依頼する

再レビュー依頼は、**新しいコミットや実質的な更新があるときだけ**送ります。

| 状況 | 再レビュー依頼する？ | 理由 |
| --- | --- | --- |
| 新しいコミットがある | はい | レビュアーに確認可能な差分があるため |
| コミットはないが、重要な説明や Issue 連携を追加した | 場合による | その返信が判断材料として重要なときだけ |
| reply-only で閉じ、コード差分がない | いいえ | reviewer ping を増やさず Step 8 に進む |

```bash
REREVIEW_BODY="$(mktemp "${TMPDIR:-/tmp}/rereview_summary.XXXXXX")" || {
  echo "再レビュー要約用の一時ファイル作成に失敗しました" >&2
  exit 1
}
cleanup_rereview_body() {
  [ -n "$REREVIEW_BODY" ] && rm -f "$REREVIEW_BODY"
}
trap cleanup_rereview_body EXIT
cat > "$REREVIEW_BODY" <<'EOF'
更新内容を確認できる状態になりました。再レビューをお願いします。
EOF

gh pr edit --add-reviewer reviewer-username
gh pr comment --body-file "$REREVIEW_BODY"
```

```powershell
$reReviewBodyPath = Join-Path $env:TEMP "rereview_summary.md"
$reReviewBody = @"
更新内容を確認できる状態になりました。再レビューをお願いします。
"@
[System.IO.File]::WriteAllText($reReviewBodyPath, $reReviewBody, [System.Text.UTF8Encoding]::new($false))

gh pr edit --add-reviewer reviewer-username
gh pr comment --body-file $reReviewBodyPath
Remove-Item $reReviewBodyPath
```

> **Values**: 成長の複利 / ニュートラル

### Step 8: graceful stop で人間の判断へ渡す

残りが non-blocking / reply-only だけなら、返信を完了した時点で止めます。  
**コメントが残っていても、blocking が片付いていれば無限に付き合わない**のがこの skill の既定です。

```markdown
人間のマージ判断に引き渡せる状態:
- blocking なレビュー対応は完了
- 今回の反復に必要な checks は完了
- 最新コミット時点で full quality gate が green
- non-blocking は返信で整理済み
- 新しいコミットがない場合、再レビュー依頼は送っていない
```

この skill は人間の代わりにマージしません。  
必要なら準備完了状況を要約して止まります。

> **Values**: ニュートラル / 余白の設計

---

## ベストプラクティス

- 修正順は `blocking -> 高価値 non-blocking -> reply-only` の順にする
- 返信だけで閉じる経路を、正式な成功パスとして扱う
- Issue は「あとで困る」「他でも効く」ものだけ作る
- asset-sensitive で判断しつつ、無関係な横展開は避ける
- 新しいコミットがないなら reviewer を再度 ping しない
- 準備完了を要約して止まり、人間の代わりにマージしない

---

## よくある落とし穴

1. **non-blocking を全部実装してしまう**  
   修正方法: reply-first を既定にし、採用理由が明確なものだけ直す。

2. **Issue を乱発する**  
   修正方法: 再利用価値、横断価値、再発防止価値がないものは返信だけで閉じる。

3. **asset-sensitive と check 範囲を混同する**  
   修正方法: コメント判断は判断テーブル、検証範囲は Step 4 で別に決める。

4. **reply-only なのに再レビュー依頼してしまう**  
   修正方法: 新しいコミットや実質更新がない限り Step 7 をスキップする。

5. **採らない提案を無返信で流す**  
   修正方法: `reject-with-reply` を使い、棄却理由を短く明示する。

---

## アンチパターン

- レビュー会話を消すために force-push する
- nitpick を止められず、PR の目的よりレビュー継続自体が目的になる
- スコープ外提案を全部 backlog に積んで認知負荷を増やす
- reviewer-facing skill の修正なのに、影響範囲を見ずに軽い確認だけで終える

---

## クイックリファレンス

### レビュー対応チェックリスト

| ステップ | アクション | 確認事項 |
| --- | --- | --- |
| 1 | コメントを分類 | コメント種類 + 資産厳しさ + disposition を確定 |
| 2 | 対応計画を作る | `fix` / `reply-only` / `defer-with-issue` が分かれている |
| 3 | 必要な修正だけ実装 | blocking と高価値 non-blocking に限定 |
| 4 | checks を実行 | 差分に必要な確認が通過 |
| 5 | 変更があるときだけコミット | 返信のみの反復では無理にコミットしない |
| 6 | すべてに返信 | 修正・棄却・保留のいずれでも理由付き返信済み |
| 7 | 必要時のみ再レビュー依頼 | 新しいコミットまたは実質更新がある |
| 8 | graceful stop | non-blocking のみなら人間判断へ引き渡す |

### 返信の既定

- **blocking**: 修正して返信
- **non-blocking**: まず返信。価値が明確なら修正
- **scope 外の不足**: まず返信。Issue は再利用価値があるときだけ
- **style / wording**: reply-only を既定

---

## FAQ

**Q: レビューコメントに同意できない場合は？**  
A: `reject-with-reply` で理由を添えて返信してください。無視はしません。

**Q: 機能不足は全部 blocking ですか？**  
A: いいえ。`scope_sensitive` です。受け入れ条件・安全性・公開品質に直結する不足だけ blocking です。

**Q: 提案がスコープ外の場合は？**  
A: まず返信で閉じます。再利用価値がある場合だけ `gh-issue-create` で Issue 化します。

**Q: reply-only でも再レビュー依頼しますか？**  
A: いいえ。新しいコミットや実質更新がないなら、通常は Step 8 に進みます。

**Q: 毎回 full quality gate を回すべきですか？**  
A: いいえ。まず focused checks です。ただし reviewer-facing skill definition や shared policy 変更など、repo guidance が要求する場合は full quality gate を追加します。

**Q: この skill は PR をマージしますか？**  
A: いいえ。返信・検証・必要時の再レビュー依頼までで止まり、マージ判断は人間に渡します。

---

## 注意点

- **reply-first を「何もしない」と誤解しない**: 返信で閉じるのも正式な対応です。
- **graceful stop を乱用しない**: blocking が残っている間は止めません。
- **Issue を親切のつもりで増やしすぎない**: backlog も認知負荷です。
- **PR の目的を見失わない**: レビュー継続自体をゴールにしません。

## リソース

- https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests
- https://cli.github.com/manual/gh_pr_review
- https://www.conventionalcommits.org/
