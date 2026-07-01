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
