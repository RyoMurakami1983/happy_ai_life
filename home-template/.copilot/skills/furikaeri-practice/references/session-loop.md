# Session loop reference

## 目的

ふりかえりを単発で終わらせず、次のセッション・共有文書・環境改善へ繋ぐ。

## ループ

1. `session-start` が前回の文脈を注入する
2. `furikaeri-practice` で YWT / KPT を作る
3. `.github/sessions/` に保存する
4. 必要なら `session-share-document` で `docs/sessions/` に整える
5. 改善種を T / TRY / Issue に逃がす
6. 次回の `session-start` がそれを拾う

## 共有文書の読みやすい型

既存の docs/sessions を見ると、次の並びが読みやすい。

- Executive Summary
- Session Notes
- 主要な学び
- 変更の要点
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
