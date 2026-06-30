# Works Promotion

`works/` は、常用前の試作、単発寄りの作業物、配布前の実験置き場です。
ここから `plugins/happy-core/` または `plugins/happy-coding/` へ移すときは、昇格基準を満たしてから行います。

## 昇格先

| 昇格先 | 使う場面 |
| --- | --- |
| `plugins/happy-core/` | authoring、評価、Git/GitHub、知識化、日常 workflow |
| `plugins/happy-coding/` | 仕様、設計、実装、review、開発環境、技術 stack 固有支援 |
| 昇格しない | 単発用途、秘密情報に依存、再利用価値未確認、保守者不在 |

## 昇格チェックリスト

- [ ] 目的が1つに絞られている。
- [ ] `SKILL.md` または agent 定義に、使う場面、手順、成功条件がある。
- [ ] `docs/SKILL_MAP.md` の基本導線へ接続できる。
- [ ] privateEval または手動確認の最小 evidence がある。
- [ ] README、docs、ADR、既存 skill と矛盾しない。
- [ ] secret、hook bypass、破壊的操作を許可していない。
- [ ] 利用者体験が変わる場合、plugin version bump と marketplace mirror 更新を同じ PR に含める。

## 判断者

昇格判断は maintainer が行います。PR review では、再利用価値、配布境界、保守責任、評価方法が読めることを確認します。

## 昇格しない場合

昇格しない試作は、`works/` に残すか、不要なら削除します。`plugins/` へ入れない理由が今後の判断に効く場合だけ、Issue または docs に短く残します。
