# Happy AI Life

このファイルは、`happy_ai_life` で繰り返し使うドメイン語彙だけを置く純粋な用語集です。
背景、思想、設計理由は `docs/PHILOSOPHY.md` と `docs/adr/` を参照します。

## Language

**skill**:
`SKILL.md` で定義された、AI agent の再利用可能な手順・判断基準。slash invocation または model invocation で実行される。
_Avoid_: prompt, template, command

**plugin**:
Copilot CLI へ配布する単位。`plugin.json`、`skills/`、必要に応じて `agents/` を含む。
_Avoid_: package, module

**works**:
常用・配布前の試作置き場。再利用価値、昇格基準、配布先が固まるまでは plugin 正本へ入れない。
_Avoid_: archive, production skill

**privateEval**:
secret を含まない評価ケースで、skill や prompt の品質を継続的に測る仕組み。実会話ログや個人情報は含めない。
_Avoid_: raw log, private data, judge

**型**:
再現可能な仕事の進め方。自由を奪うテンプレートではなく、速さ、安全性、学習の土台として使う。
_Avoid_: 固定手順, 丸写しテンプレート

**余白**:
変更、学習、回復のために意図して残す時間・設計上の空き。単なる暇や未使用時間ではない。
_Avoid_: 暇, 空き時間

**skill ecosystem**:
基本 skill、専門 skill、agent、docs、eval が孤立せず、入口、連携、評価、昇格基準を持って育つ構造。
_Avoid_: skill list

**実装契約 / implementation contract**:
`design-and-plan` の主出力。goal、success criteria、behavior list、vertical slices を含み、`implement` がそのまま着手できる形まで圧縮された handoff。
_Avoid_: 会話メモ, ふわっとした設計案

**implementation handoff**:
`design-and-plan` から `implement` へ渡す構造化成果物。repo に保存した design / plan artifact のパス、または `artifacts: conversation-only` の宣言を含める。
_Avoid_: 口頭前提, 暗黙の引き継ぎ

**vertical slice**:
1 ユーザー行動または 1 acceptance condition を主語に、必要な層を縦断する最小実装単位。
_Avoid_: DBだけ, UIだけ, 横並びの層分割

**tracer bullet**:
最初の vertical slice。入口から期待結果までの経路が本当に通るかを、最小の end-to-end で確かめる最初の 1 本。
_Avoid_: 大量実装前提の先行整備

**slice gate**:
各 vertical slice の最後に通す証拠ベースの評価関門。RED / GREEN / acceptance の証拠から `PASS` / `FAIL` / `REPLAN_REQUIRED` を判断する。
_Avoid_: 実装者の感覚だけの完了判定

**HITL / AFK**:
HITL は human-in-the-loop で、人間判断や確認が必要な slice。AFK は受け入れ条件が明確で、agent が自走しやすい slice。
_Avoid_: 曖昧な担当分担
