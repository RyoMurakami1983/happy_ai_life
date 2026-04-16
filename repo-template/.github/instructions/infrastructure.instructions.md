---
description: 外部依存 / 実機境界 / OS 連携向けの追加ルール
applyTo: "**/Infrastructure/**/*,**/Adapters/**/*,**/Drivers/**/*,**/Devices/**/*,**/Hardware/**/*,**/Serial/**/*,**/Visa/**/*,**/Daq/**/*,**/DAQ/**/*,**/IO/**/*,**/*Serial*.*,**/*Visa*.*,**/*Daq*.*,**/*DAQ*.*"
---

# Infrastructure instructions

- [repository-wide instructions](../copilot-instructions.md) を前提とし、このファイルは Serial、VISA、database、LAN、file I/O、DAQ、ADC/DAC、Clipboard、UI Automation、Win32 など外部依存境界の局所ルールだけを定義する。
- 実機、外部サービス、OS API、時刻、並行処理、アナログ信号のような壊れやすい境界では、まず failure mode と safety guard を列挙してから実装する。
- live boundary を直に握り込まず、transport / protocol / orchestration を分離し、Real / Fake / Simulation / record-replay を factory や interface で切り替えられるようにする。
- 実機未接続、対象 service 不在、通信断、タイムアウト、ノイズ、warm-up 未完了を正常系に混ぜない。状態として明示し、黙って成功扱いにしない。
- timeout、retry、cancellation、sampling interval、settling time、cooldown、debounce のような時間依存条件は hidden default にせず、契約として見える形にする。
- ノイズや瞬断を扱う場合は raw data と整形後 data を分ける。平滑化、中央値化、外れ値除去は理由と閾値を持たせ、観測値を失わない。
- database、network、device I/O はできる限り idempotent にし、途中失敗時の再試行条件と partial failure を設計で分ける。
- 対象破壊や安全リスクがある制御では、既定値を safe 側に置き、0 / off / read-only / low-output から始める。ADC / DAC や類似のアナログ出力は急変させず、段階的に signal を入れ、必要なら readback や interlock を確認する。
- 実機に副作用がある操作では、上限、下限、単位、増分、停止条件、非常停止経路をコードと docs の両方に残す。
- fake 実装は happy path だけでなく、timeout、malformed response、busy、noise、stale handle など代表的な異常系も再現できるようにする。
- test、debug、F5 実行では、live hardware 前提にせず fake / simulation を既定にできるか先に検討する。
- 外部境界での catch は抑制ではなく変換に使う。原因、対象、操作、観測値が分かる形で失敗を返す。
