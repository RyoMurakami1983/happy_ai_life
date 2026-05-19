from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy" / "guard-policy.json"
SCHEMA_PATH = ROOT / "policy" / "guard-policy.schema.json"
HOOKS_GOVERNANCE_PATH = ROOT / "archive" / "enterprise-hardening" / "docs" / "HOOKS_GOVERNANCE.md"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_policy_path(path_value: str) -> str:
    normalized = path_value.strip().replace("\\", "/")
    if normalized.endswith("/**"):
        return normalized.lower()
    return normalized.rstrip("/").lower()


def _assert_matches_schema(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        assert any(_matches_type(value, candidate) for candidate in schema_type), f"{path}: unexpected type"
    elif schema_type is not None:
        assert _matches_type(value, schema_type), f"{path}: unexpected type"

    enum = schema.get("enum")
    if enum is not None:
        assert value in enum, f"{path}: unexpected enum value {value!r}"

    any_of = schema.get("anyOf")
    if any_of is not None:
        assert any(_matches_schema_fragment(value, candidate, path) for candidate in any_of), f"{path}: no anyOf branch matched"

    not_schema = schema.get("not")
    if not_schema is not None:
        assert not _matches_schema_fragment(value, not_schema, path), f"{path}: matched forbidden schema"

    const = schema.get("const")
    if const is not None:
        assert value == const, f"{path}: unexpected const value {value!r}"

    minimum = schema.get("minimum")
    if minimum is not None:
        assert isinstance(value, int), f"{path}: minimum requires integer"
        assert value >= minimum, f"{path}: {value} < {minimum}"

    min_length = schema.get("minLength")
    if min_length is not None:
        assert isinstance(value, str), f"{path}: minLength requires string"
        assert len(value) >= min_length, f"{path}: shorter than {min_length}"

    pattern = schema.get("pattern")
    if pattern is not None:
        assert isinstance(value, str), f"{path}: pattern requires string"
        assert re.search(pattern, value) is not None, f"{path}: does not match pattern {pattern!r}"

    min_items = schema.get("minItems")
    if min_items is not None:
        assert isinstance(value, list), f"{path}: minItems requires array"
        assert len(value) >= min_items, f"{path}: fewer than {min_items} items"

    if schema.get("uniqueItems"):
        assert isinstance(value, list), f"{path}: uniqueItems requires array"
        assert len(value) == len({_json_key(item) for item in value}), f"{path}: duplicate items"

    required = schema.get("required", [])
    if required:
        assert isinstance(value, dict), f"{path}: required fields need object"
        for key in required:
            assert key in value, f"{path}: missing required key {key}"

    properties = schema.get("properties")
    if properties is not None and isinstance(value, dict):
        for key, property_schema in properties.items():
            if key in value:
                _assert_matches_schema(value[key], property_schema, f"{path}.{key}")

        additional = schema.get("additionalProperties", True)
        if additional is False:
            unexpected = set(value) - set(properties)
            assert not unexpected, f"{path}: unexpected keys {sorted(unexpected)}"

    items = schema.get("items")
    if items is not None and isinstance(value, list):
        for index, item in enumerate(value):
            _assert_matches_schema(item, items, f"{path}[{index}]")

    for clause in schema.get("allOf", []):
        if _matches_condition(value, clause.get("if", {})):
            _assert_matches_schema(value, clause["then"], path)


def _matches_type(value: Any, schema_type: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "null": value is None,
    }.get(schema_type, False)


def _matches_condition(value: Any, condition: dict[str, Any]) -> bool:
    if not condition:
        return True

    properties = condition.get("properties", {})
    if not isinstance(value, dict):
        return False

    for key, property_schema in properties.items():
        if key not in value:
            return False
        try:
            _assert_matches_schema(value[key], property_schema, f"condition.{key}")
        except AssertionError:
            return False
    return True


def _matches_schema_fragment(value: Any, schema: dict[str, Any], path: str) -> bool:
    try:
        _assert_matches_schema(value, schema, path)
    except AssertionError:
        return False
    return True


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def test_guard_policy_matches_schema() -> None:
    policy = _read_json(POLICY_PATH)
    schema = _read_json(SCHEMA_PATH)

    _assert_matches_schema(policy, schema)


def test_guard_policy_schema_rejects_future_schema_version() -> None:
    schema = _read_json(SCHEMA_PATH)
    invalid_policy = _read_json(POLICY_PATH)
    invalid_policy["schemaVersion"] = 2

    try:
        _assert_matches_schema(invalid_policy, schema)
    except AssertionError:
        return

    raise AssertionError("schemaVersion 2 unexpectedly accepted by policy schema")


def test_guard_policy_covers_current_boundary_rules() -> None:
    policy = _read_json(POLICY_PATH)

    protected_paths = {entry["path"] for entry in policy["protectedPaths"]}
    assert protected_paths == {
        ".github/hooks/**",
        ".githooks/**",
        ".github/workflows/**",
        ".github/mcp.json",
        ".mcp.json",
        ".gitleaks.toml",
        "policy/guard-policy.json",
        "policy/guard-policy.schema.json",
        "$HOME/.copilot/maintenance-mode.json",
    }

    deny_rule_ids = {entry["id"] for entry in policy["denyCommandRules"]}
    assert {
        "maintenance-mode-manual-only",
        "git-hooks-no-verify",
        "git-hooks-path-change",
        "git-hooks-update-index-bypass",
        "git-push-force",
        "git-commit-secret-scan",
        "git-push-secret-scan",
        "gh-pr-create-secret-scan",
        "git-reset-hard",
        "powershell-encoded-command",
        "invoke-expression",
        "curl-pipe-sh",
        "wget-pipe-sh",
    }.issubset(deny_rule_ids)


def test_guard_policy_has_unique_protected_path_ids_and_paths() -> None:
    policy = _read_json(POLICY_PATH)

    protected_ids = [entry["id"] for entry in policy["protectedPaths"]]
    normalized_paths = [_normalize_policy_path(entry["path"]) for entry in policy["protectedPaths"]]

    assert len(protected_ids) == len(set(protected_ids))
    assert len(normalized_paths) == len(set(normalized_paths))


def test_guard_policy_schema_rejects_file_scope_path_with_directory_wildcard() -> None:
    schema = _read_json(SCHEMA_PATH)
    invalid_path_rule = {
        "id": "file-with-wildcard",
        "path": ".github/hooks/**",
        "scope": "file",
        "action": "ask",
        "maintenanceScope": "protectedPathEdit",
    }

    try:
        _assert_matches_schema(invalid_path_rule, schema["properties"]["protectedPaths"]["items"], "$.protectedPaths[0]")
    except AssertionError:
        return

    raise AssertionError("file-scope protected path unexpectedly accepted directory wildcard")


def test_guard_policy_schema_rejects_file_scope_path_with_backslash_directory_wildcard() -> None:
    schema = _read_json(SCHEMA_PATH)
    invalid_path_rule = {
        "id": "file-with-backslash-wildcard",
        "path": ".github\\hooks\\**",
        "scope": "file",
        "action": "ask",
        "maintenanceScope": "protectedPathEdit",
    }

    try:
        _assert_matches_schema(invalid_path_rule, schema["properties"]["protectedPaths"]["items"], "$.protectedPaths[0]")
    except AssertionError:
        return

    raise AssertionError("file-scope protected path unexpectedly accepted backslash directory wildcard")


def test_guard_policy_schema_rejects_whitespace_only_protected_path_fields() -> None:
    schema = _read_json(SCHEMA_PATH)
    invalid_rule = {
        "id": " ",
        "path": "   ",
        "scope": "file",
        "action": "ask",
        "maintenanceScope": "protectedPathEdit",
    }

    try:
        _assert_matches_schema(invalid_rule, schema["properties"]["protectedPaths"]["items"], "$.protectedPaths[0]")
    except AssertionError:
        return

    raise AssertionError("protected path unexpectedly accepted whitespace-only id/path")


def test_guard_policy_schema_rejects_whitespace_only_path_property_name() -> None:
    schema = _read_json(SCHEMA_PATH)

    try:
        _assert_matches_schema(["path", "   "], schema["properties"]["pathPropertyNames"], "$.pathPropertyNames")
    except AssertionError:
        return

    raise AssertionError("pathPropertyNames unexpectedly accepted whitespace-only entry")


def test_guard_policy_has_unique_deny_rule_ids() -> None:
    policy = _read_json(POLICY_PATH)

    deny_rule_ids = [entry["id"] for entry in policy["denyCommandRules"]]

    assert len(deny_rule_ids) == len(set(deny_rule_ids))


def test_guard_policy_blocks_rm_long_option_root_and_current_directory_forms() -> None:
    policy = _read_json(POLICY_PATH)
    patterns = [
        re.compile(entry["pattern"], re.IGNORECASE)
        for entry in policy["denyCommandRules"]
        if entry["kind"] == "pattern" and entry["matchAgainst"] == "normalized"
    ]

    blocked_commands = [
        "rm --recursive --force /",
        "rm --force --recursive .",
        "rm -r --force ./",
        "cmd /c rm --recursive --force /",
        'bash -c "rm -rf /"',
        "sh -c 'rm --recursive --force /'",
        'powershell -Command "rm -rf /"',
    ]
    allowed_commands = [
        "rm --recursive --force /tmp/build",
        "sudo rm --force --recursive /tmp/build",
    ]

    for command in blocked_commands:
        assert any(pattern.search(command) for pattern in patterns), command
    for command in allowed_commands:
        assert not any(pattern.search(command) for pattern in patterns), command


def test_guard_policy_schema_rejects_specialized_rule_with_pattern_fields() -> None:
    schema = _read_json(SCHEMA_PATH)
    invalid_rule = {
        "id": "specialized-with-pattern",
        "kind": "specialized",
        "description": "should be rejected",
        "matchAgainst": "normalized",
        "pattern": "git reset --hard",
    }

    try:
        _assert_matches_schema(invalid_rule, schema["properties"]["denyCommandRules"]["items"], "$.denyCommandRules[0]")
    except AssertionError:
        return

    raise AssertionError("specialized deny rule unexpectedly accepted pattern fields")


def test_guard_policy_schema_rejects_whitespace_only_pattern_rule_fields() -> None:
    schema = _read_json(SCHEMA_PATH)
    invalid_rule = {
        "id": " ",
        "kind": "pattern",
        "description": "valid description",
        "matchAgainst": "normalized",
        "pattern": "   ",
    }

    try:
        _assert_matches_schema(invalid_rule, schema["properties"]["denyCommandRules"]["items"], "$.denyCommandRules[0]")
    except AssertionError:
        return

    raise AssertionError("pattern deny rule unexpectedly accepted whitespace-only id/pattern")


def test_guard_policy_schema_rejects_whitespace_only_tool_name() -> None:
    schema = _read_json(SCHEMA_PATH)

    try:
        _assert_matches_schema(["   "], schema["properties"]["toolNames"]["properties"]["shell"], "$.toolNames.shell")
    except AssertionError:
        return

    raise AssertionError("toolNames.shell unexpectedly accepted whitespace-only entry")


def test_guard_policy_tool_names_match_runtime_defaults() -> None:
    policy = _read_json(POLICY_PATH)

    assert policy["toolNames"]["shell"] == ["bash", "powershell"]
    assert policy["toolNames"]["fileWrite"] == ["create", "edit"]


def test_guard_policy_docs_reference_policy_as_source_of_truth() -> None:
    hooks_governance = HOOKS_GOVERNANCE_PATH.read_text(encoding="utf-8")

    assert "policy/guard-policy.json" in hooks_governance
    assert "policy/guard-policy.schema.json" in hooks_governance
    assert "source of truth" in hooks_governance
