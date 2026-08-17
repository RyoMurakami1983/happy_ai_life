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
secret を含まない評価ケースの設計・保管・昇格判断を担う層。評価の実行そのものではなく、再利用できる `evals/<skill-id>/` の基準と資産を扱う。
_Avoid_: raw log, private data, judge, benchmark runner

**型**:
再現可能な仕事の進め方。自由を奪うテンプレートではなく、速さ、安全性、学習の土台として使う。
_Avoid_: 固定手順, 丸写しテンプレート

**余白**:
変更、学習、回復のために意図して残す時間・設計上の空き。単なる暇や未使用時間ではない。
_Avoid_: 暇, 空き時間

**skill ecosystem**:
基本 skill、専門 skill、agent、docs、eval が孤立せず、入口、連携、評価、昇格基準を持って育つ構造。
_Avoid_: skill list

**AGENTS.md**:
repo root に置く cross-agent brief。repo の役割、主要 command、boundary、source of truth への入口を短く示す。
_Avoid_: skill の詳細手順, 長い設計理由, README の置き換え

**disable-model-invocation**:
orchestration 親が「自分で実行する unit ではなく、route / handoff に徹する」と示す frontmatter。Copilot CLI では可視性や manual-only 動作の保証としては扱わない。
_Avoid_: slash 非表示フラグ, manual-only guarantee

**learnings**:
失敗や繰り返しの修正から抽出した、短く一般化された再発防止ルール。会話ログではなく、docs や instructions へ書き戻して再利用する。
_Avoid_: raw transcript, 失敗ログの丸写し, 長いふりかえり本文

**family router**:
同じ技術領域の公開入口を 1 つに集約し、配下の internal sub-skill へ振り分ける親 skill。初見利用者には入口を減らしつつ、leaf には親文脈つきの短い名前を許せる。
_Avoid_: flat skill list, independent top-level duplicates

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
