# Session loop reference

## 目的

ふりかえりを単発で終わらせず、次のセッション・共有文書・環境改善へ繋ぐ。

## ループ

1. 公式 session data、必要に応じて `/chronicle standup`、または session story から作業を思い出す
2. `furikaeri-practice` でセッションストーリーをほどき、YWT / KPT を選ぶ
3. 1 日の終わりは複数 repo / 複数 session を 1 つの日次ふりかえりへまとめる
4. ふりかえりを `.copilot/docs/furikaeri/` に主保存し、必要なものだけ `docs/furikaeri/` に共有する
5. 改善種を T / TRY / Issue / 条件付き skill 改善提案 に逃がす
6. 次回は session data、日次ふりかえり、明示された repo docs を材料に再開する

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
- `/share file session` は raw session export が必要なときだけ明示的に使う

## 良い循環

良いふりかえりは、次の 3 つを同時に満たす。

- 次回の自分が動きやすい
- 共有すると他人にも使える
- 環境が少し良くなる
