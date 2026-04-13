# Session loop reference

## 目的

ふりかえりを単発で終わらせず、次のセッション・共有文書・環境改善へ繋ぐ。

## ループ

1. `session-start` が前回の文脈を注入する
2. `furikaeri-practice` でセッションストーリーをほどき、YWT / KPT を選ぶ
3. `.github/sessions/` は continuity 用の private log として残る
4. 共有できるふりかえりを `docs/furikaeri/` と `.copilot/docs/furikaeri/` に保存する
5. 改善種を T / TRY / Issue / 条件付き skill 改善提案 に逃がす
6. 次回の `session-start` が repo の `docs/furikaeri/` を拾う

## 共有文書の読みやすい型

既存の docs/furikaeri では、次の並びが読みやすい。

- Executive Summary
- Session Story
- Reflection
- Session Notes
- Next Steps

短い要約から始め、学びと次の一手に繋げると再利用しやすい。

## 保存時の方針

- 事実は Y / Keep に寄せる
- 解釈は W / Problem に寄せる
- 未来の行動は T / Try に寄せる
- 環境改善は Issue か skill 更新に繋ぐ

## 良い循環

良いふりかえりは、次の 3 つを同時に満たす。

- 次回の自分が動きやすい
- 共有すると他人にも使える
- 環境が少し良くなる
