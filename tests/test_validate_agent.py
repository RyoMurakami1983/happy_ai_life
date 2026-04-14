from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home-template" / ".copilot" / "skills" / "copilot-authoring-beta" / "_eval" / "scripts" / "validate_agent.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_agent_script", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_agent_accepts_valid_agent_markdown(tmp_path: Path) -> None:
    module = _load_module()
    agent_path = tmp_path / "sample-agent.agent.md"
    agent_path.write_text(
        """---
name: sample-agent
description: >
  変更差分を点検して改善点を返す。Use when: agent の草案品質を確認したいとき。
tools:
  - read
  - search
model: gpt-5.4
disable-model-invocation: false
user-invocable: true
---

# Sample Agent

この agent は草案の構造を読み、なぜその修正が効くかも返します。

## 役割

- 草案の構造不備を見つける
- 改善理由を利用者に返す

## 非責務

- 実装を直接変更する

## 品質判断の原則

この原則は docs/PHILOSOPHY.md の思想を品質判断に落とし込んだものです。

### 1. 根拠で語る

なぜこの改善が効くかを説明する。

## レビュープロセス

### Step 1: 読み取る

草案と周辺定義を確認する。

### Step 2: 判断する

不足と強みを整理する。

## 出力の型

改善提案を箇条書きで返す。

## 注意点

- 1 件の失敗だけで過剰適合しない。

## 完了条件

- 改善点と理由を返している。

## 関連スキル

- `copilot-authoring-beta`
""",
        encoding="utf-8",
    )

    report = module.validate(agent_path, "L2")

    assert report.critical_passed is True
    assert report.recommended_pass_count == report.recommended_total


def test_validate_agent_limits_distributed_agents_to_three() -> None:
    """Phase 3: distributed custom agents stay within the reserved 3-slot envelope."""
    agents_dir = ROOT / "home-template" / ".copilot" / "agents"
    assert agents_dir.exists()
    agent_names = [path.name for path in sorted(agents_dir.glob("*.agent.md"))]
    assert "tdd-coder.agent.md" in agent_names
    assert len(agent_names) <= 3


def test_validate_agent_real_tdd_coder_markdown() -> None:
    module = _load_module()
    agent_path = ROOT / "home-template" / ".copilot" / "agents" / "tdd-coder.agent.md"

    report = module.validate(agent_path, "L2")

    assert report.critical_passed is True
    assert report.recommended_pass_count == report.recommended_total


def test_tdd_coder_handoff_contract_mentions_test_and_runtime_fields() -> None:
    agent_path = ROOT / "home-template" / ".copilot" / "agents" / "tdd-coder.agent.md"
    content = agent_path.read_text(encoding="utf-8")

    assert "- Test artifact path:" in content
    assert "- Test command:" in content
    assert "- Runtime launch command:" in content


def test_validate_agent_rejects_missing_principles_only(tmp_path: Path) -> None:
    module = _load_module()
    agent_path = tmp_path / "missing-principles.agent.md"
    agent_path.write_text(
        """---
name: missing-principles
description: >
  変更差分を点検して改善点を返す。Use when: agent の草案品質を確認したいとき。
tools:
  - read
  - search
model: gpt-5.4
disable-model-invocation: false
user-invocable: true
---

# Missing Principles Agent

この agent は草案の構造を読み、なぜその修正が効くかも返します。

## 役割

- 草案の構造不備を見つける
- 改善理由を利用者に返す

## 非責務

- 実装を直接変更する

## プロセス

### Step 1: 読み取る

草案と周辺定義を確認する。

### Step 2: 判断する

不足と強みを整理する。

## 出力の型

改善提案を箇条書きで返す。

## 注意点

- 1 件の失敗だけで過剰適合しない。

## 完了条件

- 改善点と理由を返している。

## 関連スキル

- `copilot-authoring-beta`
""",
        encoding="utf-8",
    )

    report = module.validate(agent_path, "L1")

    assert report.critical_passed is False
    failed_checks = {check.id for check in report.critical if not check.passed}
    assert "C4" in failed_checks


def test_validate_agent_rejects_missing_required_structure(tmp_path: Path) -> None:
    module = _load_module()
    agent_path = tmp_path / "broken-agent.agent.md"
    agent_path.write_text(
        """---
name: broken-agent
description: 草案を確認する agent
tools:
  - read
model: gpt-5.4
disable-model-invocation: false
user-invocable: true
---

# Broken Agent

## 役割

- 草案を見る
""",
        encoding="utf-8",
    )

    report = module.validate(agent_path, "L1")

    assert report.critical_passed is False
    failed_checks = {check.id for check in report.critical if not check.passed}
    assert {"C3", "C4", "C5"} <= failed_checks
