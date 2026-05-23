# Issue discovery from furikaeri

## 目的

KPT で見えた Problem / Try を、必要なものだけ GitHub Issue 候補に変える。ふりかえり本文は人間向けの記録として保ち、追跡すべき改善だけを `gh-issue-create` に渡す。

## Issue 候補にする条件

- 再発しそう、または複数 repo / 複数 session に効く
- 対象が skill / hook / docs / workflow / script のどれかに置ける
- Acceptance Criteria を観測可能に書ける
- 今すぐ直すより、追跡した方が安全

## Issue にしないもの

- その場限りの感想
- owner や対象が曖昧なままの不満
- すでに今回の作業で解決したこと
- 「気をつける」だけで完了判定がないもの

## 候補の型

```markdown
## 改善 Issue 候補

### [タイトル案]
- 背景:
- Problem:
- Try:
- 対象:
- Acceptance Criteria:
- 優先度:
- `gh-issue-create` へ渡すか:
```

## 優先度の目安

| 優先度 | 目安 |
| --- | --- |
| High | 安全性、情報漏洩、破壊的操作、再発する重大な出戻り |
| Medium | 複数 session で効く workflow / skill / docs 改善 |
| Low | 読みやすさ、表現整理、将来の補助 |

## gh-issue-create へ渡すとき

渡す前に次を満たす。

1. タイトルが具体的
2. Problem が人ではなくプロセス・道具・条件に向いている
3. Acceptance Criteria が第三者に判定できる
4. 公開 repo に出せる内容へ匿名化されている
