# DeepReview Checklist

必要な観点だけを選んで使うための checklist です。

## 1. 一次情報

- 関連 Issue / PR / docs / official reference を読んだか
- 推測で埋めた仕様がないか
- comment や docstring の約束を確認したか

## 2. Source of Truth

- 編集対象は正本か
- mirror / template / generated file を誤って直していないか
- 同責務の実装が別ディレクトリに重複していないか

## 3. 非破壊性

- update / replace の境界が安全か
- handwritten region や legacy data を壊さないか
- marker なしケースや empty state を見たか
- DryRun / warning / exit code が実装と一致しているか

## 4. 配布経路

- `scripts\sync-to-home.ps1` / `scripts\sync-to-repo.ps1` でどこへ配布されるか説明できるか
- home / repo / template の責務が混ざっていないか
- unsupported path に実装を置いていないか

## 5. 回帰確認

- 変更に対応する既存 test / lint / validate / DryRun を実行したか
- 新しい分岐に対する確認手段を残したか
- 再 review を 1 回回したか

## 6. Reviewer 先読み

- 今回の修正で次に疑われる点を 2〜3 手先まで見たか
- 説明文と実装のズレがないか
- 高コスト model や重い workflow を不要に既定化していないか
