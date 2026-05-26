# Grill Result Template

`grill-with-docs` 完了時は、会話出力と同じ内容を `docs/grill_results/NNN_GRILL_WITH_DOCS_RESULT.md` に保存します。`NNN` は同じ案件の `docs/design/NNN_TECHNICAL_DESIGN.md` と `docs/plan/NNN_PLAN.md` で共有します。

```markdown
# Grill with Docs Result

## 対象

[今回 grill した対象]

## 読んだ source of truth

- [docs / code / ADR / test]

## 解決した用語

- **[canonical term]**: [どう定義したか]

## 更新した docs

- [更新した CONTEXT.md / 追加した artifact]

## ADR 判断

- [ADR が必要 / 不要。その理由]

## 残った質問

- [残った Unknown。なければ「なし」]

## 推奨される次工程

- `design-and-plan` / `prototype` / `implement`
```
