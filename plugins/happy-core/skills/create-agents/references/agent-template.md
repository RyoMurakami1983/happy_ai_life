# Agent Template

agent.md を作成する際の雛形です。`<...>` の箇所を埋めて使います。

## Frontmatter

```yaml
---
name: <kebab-case-name>
description: >
  <1〜2文で何をするエージェントか。>
  Use when: <いつ使うか>。
tools:
  - read
  - search
model: <model-id>
disable-model-invocation: false
user-invocable: true
---
```

### Frontmatter フィールド

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `name` | ✓ | kebab-case。ファイル名の `<name>.agent.md` と一致させる |
| `description` | ✓ | `>` で折り返し、`Use when:` トリガー句を含める |
| `tools` | ✓ | `read`, `search`, `execute`, `edit` から最小限を選ぶ |
| `model` | ✓ | ユーザーと相談して決定する |
| `disable-model-invocation` | ✓ | 通常は `false` |
| `user-invocable` | ✓ | 通常は `true` |

## 本文構成

```markdown
# <Agent Title>

<1〜2文でこのエージェントの目的を説明する。>

## 役割

- <このエージェントが何をするか（4項目程度）>

## 非責務

- <このエージェントがやらないこと（3項目程度）>

## <領域名>の原則

この原則は `docs/PHILOSOPHY.md` の思想を<領域名>に落とし込んだものです。

### 1. <原則名>

<なぜこの原則がこの領域で効くかを prose で説明する。>

### 2. <原則名>
...

## プロセス

### Step 1: <動詞で始まる>

<何をするか、なぜ必要か。>

確認すること:
- <確認項目>

### Step 2: <動詞で始まる>
...

## 出力の型

<出力フォーマットのテンプレートを示す。>

## 注意点

- <やりがちな失敗とその回避策。なぜ安全な選択のほうが効くかを説明する。>

## 完了条件

- <このエージェントの出力が満たすべき条件>
```

## 配置規約

- ファイル名: `<name>.agent.md`（単数形の `.agent.md`）
- 配置先: `plugins/happy-coding/agents/`
- `name` フィールドとファイル名の `<name>` 部分を一致させる
