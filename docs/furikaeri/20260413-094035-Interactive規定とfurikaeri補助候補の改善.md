# Interactive規定とfurikaeri補助候補の改善

## Executive Summary

- `furikaeri-practice` と共有保存導線の統合は、最初の計画から大きな詰まりなく進んだ。
- 一方で、PLAN 後に autopilot を勧める導線は、プレミアムリクエスト消費が見えにくいまま押しやすく、現運用には合わないことが明確になった。
- 次の改善軸は、`copilot-instructions.md` の Interactive 規定追加と、ふりかえりでユーザー回答後に補助候補を出す対話強化である。

## Session Story

- `furikaeri-practice` と共有保存 skill の統合を実施した。
- 2 つの skill は密接につながっていたが、保存先が分かれていて扱いづらかった。
- 実装後のふりかえりで、保存先の摩擦に加えて、PLAN 後の autopilot 推奨導線にも運用上の違和感があると整理した。

## Reflection

### Keep

- 最初の計画からスムーズに進んだ。
- 統合対象が密接で、1 本化の方向が自然だった。
- hook / sync / docs まで一気に揃えられた。

### Problem

- 保存先の分断で、2 skill をまたぐ扱いがわかりにくかった。
- PLAN 後に autopilot を勧める導線が、現在の運用方針と合っていない。
- autopilot の消費実態が実行後か GitHub の利用確認サイトでないと見えにくい。

### Try

- `copilot-instructions.md` に「PLAN 後は Interactive を既定とし、autopilot は推奨しない」を追加する。
- `furikaeri-practice` に、ユーザー回答後の補助候補提示を追加する。

### 5つのなぜ

1. なぜ問題か: プレミアムリクエストが異常に利用されていて危険と感じたため。
2. なぜそう考えたか: 裏側で agent 同士が質問し、リクエストを消費しているように見えたため。
3. なぜ見えにくいか: autopilot は完了後でないと分からず、GitHub の利用確認サイトでないと実体把握しづらいため。
4. なぜ設計が合わないか: Recommend され、そのまま押せる状態になっており、Interactive 規定のほうが良いと感じたため。
5. なぜ Interactive が合うか: 自分がプロンプトを打ったときだけ消費し、無駄な PR 消費を抑えられるため。

### SMART

- **Specific**: `copilot-instructions.md` に Interactive 規定を追加する。
- **Measurable**: PLAN 後に autopilot を勧めない文言が明記されている状態にする。
- **Achievable**: 文書変更として小さく実施できる。
- **Relevant**: プレミアムリクエスト消費の見えにくさと過剰利用への懸念に直結する。
- **Time-bound**: 次回の改善セッションで反映する。

### skill 改善提案

- `furikaeri-practice` は、ユーザーが Keep / Problem / Try を出したあとに、アシスタント側の補助候補を 1〜3 件だけ提示する。

## Session Notes

- 今回の trial 保存先は `docs/furikaeri/` のみとした。
- 問題は大きな詰まりではなく、運用と消費制御の摩擦として表面化した。

## Next Steps

- `copilot-instructions.md` に Interactive 規定を追加する。
- `furikaeri-practice` に補助候補提示フローを追加する。
