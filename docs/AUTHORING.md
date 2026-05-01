# Authoring Guide: Creating Skills, Agents, and Instructions

<!-- TODO: 詳細な Authoring ガイドを記述
構成：
- Concepts（Skills / Agents / Instructions の違い）
- ワークフロー（design-workshop → PLAN → implement → submit）
- ベストプラクティス
- 例とテンプレート

参考: Rubber Duck agent からの提案、現在の README Development セクション
-->

## Concepts

### Skills

Reusable, self-contained tools that Copilot can invoke.

<!-- TODO: 詳細 -->

### Agents

Autonomous systems that use multiple skills and maintain state.

<!-- TODO: 詳細 -->

### Instructions

Persistent guidance for Copilot (repo-wide or path-specific).

<!-- TODO: 詳細 -->

## Authoring Workflow

### 1. Design

Use `/design-workshop` to explore architectural options.

### 2. Plan

Use PLAN mode to break down implementation.

### 3. Implement

Use narrow specialists like `tdd-coder` for complex tasks.

### 4. Submit

Use `copilot-authoring` skill to validate and package.

<!-- TODO: 詳細ステップ -->

## Best Practices

### Skills

<!-- TODO: Skills のベストプラクティス -->

### Agents

<!-- TODO: Agents のベストプラクティス -->

### Instructions

<!-- TODO: Instructions のベストプラクティス -->

## Examples

<!-- TODO: 実装例 -->

## See also

- [Development](DEVELOPMENT.md)
- [Reference](REFERENCE.md)
