# Agent Evaluation Guide

現在の配布対象 custom agent は `tdd-coder` だけです。  
skills を入口、PLAN mode を計画の正本に保つ方針は維持したまま、TDD 実装専用の narrow specialist だけを評価対象にします。

## 現在の方針

- 仕様整理の入口は `spec-workshop`
- 構造判断と設計 handoff は `design-workshop`
- 実装計画・フェーズ分割・段取り整理は PLAN mode
- TDD 実装の specialist は `tdd-coder`
- 既存コードの結合分析は `modularity-review`
- 実装と review は built-in 機能またはオーケストレーター

## `tdd-coder` をどう見るか

- **見るポイント**: 前提不足なら止まれるか、failing test を先に固定するか、最小実装に留まれるか
- **見ないポイント**: 仕様設計の巧拙、広い review の深さ、計画の網羅性
- **失格条件**: 受け入れ条件が曖昧なまま実装を始める、複数責務を一度に抱える、review 役まで引き受ける

## 関連文書

- `docs/agent-dispatch-options.md`
- `.github/copilot-instructions.md`
- `docs/adr/agent-dispatch-rules.md`
