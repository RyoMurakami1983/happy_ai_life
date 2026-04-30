# Quick YWT reference

## 目的

日常のセッション終了を短く閉じる。Y は事実を厚めに、W は学びをはっきり、T は次の一手に絞る。複雑な skill 利用や出戻りが見えたら、この形式は使わず KPT へ切り替える。

## Y（やったこと）

Y は「何をしたか」を具体化する。単なる要約ではなく、次の材料になる粒度で書く。

### 観点

- 作業したこと
- 変更したファイルや機能
- 確認したこと、通ったテスト、見つかった差分
- 詰まりや戻りがあればその事実
- 環境や運用に残すべき種

### 書き方のコツ

- 箇条書きは少し細かくしてよい
- 手順よりも「何が変わったか」を残す
- 事実と判断を分ける

## W（わかったこと）

W は学び・気づき・予想外の事実を書く。

- うまくいった理由
- 想定との差分
- 次回に効く判断基準
- 詰まりや出戻りがあった場合の原因候補

### Trouble / backtrack があるとき

W だけで終わらせず、Deep の KPT に移行して Problem と Try を分ける。複数 skill をまたいだり、判断をやり直したりした場合も同様。

## T（つぎにやること）

T は次のセッションの入口。

- 最大 3 件を目安にする
- 実行可能な粒度にする
- `TRY` を併記してもよい
- 「気をつける」より「試すこと」「直すこと」を書く

### 例

```markdown
### T（つぎにやること）
- furikaeri の対話フローを 1 回通して確認する
- docs/furikaeri の naming と output shape を揃える
- TRY: home の .copilot/docs/furikaeri にも同じ文書を保存する
```

## SMART への接続

Quick でも最後は SMART に落とす。

- Specific: 次に何をするか 1 文で言える
- Measurable: 完了判定が見える
- Achievable: 次回セッションで手が届く
- Relevant: 今回の学びに直結する
- Time-bound: 次回までの動きに繋がる

## 保存文書の型

docs/furikaeri に残すなら、次の形が読みやすい。

- Executive Summary
- Session Story
- Reflection
- Session Notes
- Next Steps

既存の session 文書からは、短い要約 → 学び → 次の一手 の順が安定しやすい。
