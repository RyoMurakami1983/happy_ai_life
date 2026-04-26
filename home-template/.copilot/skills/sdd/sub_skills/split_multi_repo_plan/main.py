"""
split_multi_repo_plan: Convert unified architecture to per-repo plans.

Phase 1 Implementation - Core functionality:
- DAG construction from repo dependencies
- Cycle detection using Tarjan's algorithm
- Contract validation (provides/requires matching)
- Per-repo plan.md generation with YAML front-matter
- Placeholder checksums (calculated on Phase 3 contract_verify)
"""

from __future__ import annotations

from typing import Any


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected in repos."""

    pass


class ContractMismatchError(Exception):
    """Raised when provides/requires artifacts don't match."""

    pass


def build_dependency_graph(repos: list[dict[str, Any]]) -> dict[str, list[str]]:
    """
    Build a directed acyclic graph (DAG) from repos.

    Args:
        repos: List of repo dicts with 'name' and optional 'requires' field

    Returns:
        Dict where keys are repo names and values are lists of repo names they depend on
    """
    graph: dict[str, list[str]] = {}

    # Initialize all repos as nodes
    for repo in repos:
        graph[repo["name"]] = []

    # Add edges based on requires relationships
    for repo in repos:
        if "requires" in repo:
            for req in repo["requires"]:
                source_repo = req.get("source_repo")
                if source_repo:
                    graph[repo["name"]].append(source_repo)

    return graph


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """
    Detect cycles in dependency graph using DFS.

    Args:
        graph: Dict where keys are nodes and values are lists of dependencies

    Returns:
        List of cycles (each cycle is a list of node names)
    """
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles


def validate_contracts(repos: list[dict[str, Any]]) -> list[str]:
    """
    Validate that all required artifacts are provided by some repo.

    Args:
        repos: List of repo dicts with 'name', optional 'requires', and 'provides'

    Returns:
        List of error messages (empty if all contracts valid)
    """
    errors: list[str] = []

    # Build a map of what each repo provides
    provides_map: dict[str, dict[str, Any]] = {}
    for repo in repos:
        repo_name = repo["name"]
        provides_map[repo_name] = {}
        if "provides" in repo:
            for artifact in repo["provides"]:
                key = (artifact["artifact"], artifact.get("version"))
                provides_map[repo_name][key] = artifact

    # Check all requires are satisfied
    for repo in repos:
        if "requires" in repo:
            for req in repo["requires"]:
                source_repo = req.get("source_repo")
                artifact_name = req.get("artifact")
                version = req.get("version")

                if not source_repo or source_repo not in provides_map:
                    errors.append(
                        f"Repo '{repo['name']}' requires artifact '{artifact_name}' "
                        f"from unknown repo '{source_repo}'"
                    )
                    continue

                key = (artifact_name, version)
                if key not in provides_map[source_repo]:
                    errors.append(
                        f"Repo '{source_repo}' does not provide artifact "
                        f"'{artifact_name}' version '{version}' required by '{repo['name']}'"
                    )

    return errors


def calculate_checksums(
    provides: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Prepare artifacts with placeholder checksums.

    Checksums are set to null as placeholders. They will be calculated
    by contract_verify on first execution (Phase 3 checkpoint).

    Args:
        provides: List of artifact dicts with 'artifact', 'path', 'version'

    Returns:
        List of artifact dicts with 'checksum' field set to None
    """
    result: list[dict[str, Any]] = []

    for item in provides:
        # Create a new dict with the placeholder checksum
        artifact_with_checksum = dict(item)
        # Set checksum to None (will be null in YAML)
        artifact_with_checksum["checksum"] = None

        result.append(artifact_with_checksum)

    return result


def generate_plan_md(
    repo: dict[str, Any],
    all_repos: list[dict[str, Any]],
) -> str:
    """
    Generate YAML front-matter + narrative markdown for repo.

    New schema (Phase 1 fix):
    - dependencies.contracts.provides: artifacts this repo produces
    - dependencies.contracts.requires: artifacts this repo consumes (with relative paths)
    - checksums: null (placeholder, filled by contract_verify on Phase 3)

    Args:
        repo: Current repo dict
        all_repos: All repos in the unified architecture

    Returns:
        Markdown string with YAML front-matter and narrative
    """
    repo_name = repo["name"]
    provides = repo.get("provides", [])
    requires = repo.get("requires", [])

    # Generate checksums (now placeholders)
    provides_with_checksums = calculate_checksums(provides)

    # Build related_repositories list (repos this one depends on or that depend on it)
    related_repos = set()
    for req in requires:
        if "source_repo" in req:
            related_repos.add(req["source_repo"])

    # Also include repos that require this one
    for other_repo in all_repos:
        if other_repo["name"] != repo_name:
            for req in other_repo.get("requires", []):
                if req.get("source_repo") == repo_name:
                    related_repos.add(other_repo["name"])

    # Helper function to calculate relative path from one repo to another
    def get_relative_path(source_repo_name: str, target_path: str) -> str:
        """Calculate relative path from current repo to source repo's artifact."""
        return f"../{source_repo_name}/{target_path}"

    # Build YAML front-matter with new schema (contracts.provides + contracts.requires)
    yaml_fm = f"""---
project_context:
  repository: "{repo_name}"
  related_repositories: {sorted(list(related_repos)) if related_repos else "[]"}

dependencies:
  blocking: {sorted([req.get('source_repo', '') for req in requires]) if requires else "[]"}
  contracts:
    provides:
"""

    # Add provides section with null checksums
    if provides_with_checksums:
        for artifact in provides_with_checksums:
            yaml_fm += f"""      - artifact: "{artifact.get('artifact', '')}"
        path: "{artifact.get('path', '')}"
        checksum: null
        version: "{artifact.get('version', '')}"
"""
    else:
        yaml_fm += "      []"

    # Add requires section with relative paths
    yaml_fm += "    requires:\n"
    if requires:
        for req in requires:
            source_repo = req.get("source_repo", "")
            artifact_name = req.get("artifact", "")
            version = req.get("version", "")
            
            # Find the actual path from provides of source repo
            source_artifact_path = ""
            for source in all_repos:
                if source["name"] == source_repo:
                    for provided in source.get("provides", []):
                        if provided.get("artifact") == artifact_name:
                            source_artifact_path = provided.get("path", "")
                            break
                    break
            
            relative_path = get_relative_path(source_repo, source_artifact_path)
            yaml_fm += f"""      - source_repo: "{source_repo}"
        artifact: "{artifact_name}"
        path: "{relative_path}"
        checksum: null
        version: "{version}"
"""
    else:
        yaml_fm += "      []\n"

    yaml_fm += "\n---\n\n"

    # Build narrative section
    narrative = f"# {repo_name.capitalize()} Implementation Plan\n\n"
    narrative += "## Phase Breakdown\n\n"
    narrative += "### Phase 1: Setup and Dependencies\n\n"

    if requires:
        narrative += "#### Blocking Dependencies\n\n"
        for req in requires:
            narrative += (
                f"- Requires `{req.get('artifact', '')}` "
                f"(v{req.get('version', '')}) from `{req.get('source_repo', '')}`\n"
            )
        narrative += "\n"

    if provides:
        narrative += "#### Provided Artifacts\n\n"
        for artifact in provides:
            narrative += (
                f"- Provides `{artifact.get('artifact', '')}` "
                f"(v{artifact.get('version', '')}) at `{artifact.get('path', '')}`\n"
            )
        narrative += "\n"

    narrative += "## Acceptance Criteria\n\n"
    narrative += "- [ ] All blocking dependencies resolved\n"
    narrative += "- [ ] Provided artifacts generated and validated\n"
    narrative += "- [ ] Integration tests passing with dependent repos\n\n"

    narrative += "## Notes\n\n"
    narrative += "This plan was auto-generated from the unified architecture.\n"
    narrative += "Checksums are calculated on first impl-and-ship execution (contract_verify checkpoint).\n"

    return yaml_fm + narrative


def split_multi_repo_plan(
    unified_architecture: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Split unified architecture into per-repo plan.md files.

    Main entry point: takes unified architecture and generates independent plans.

    Args:
        unified_architecture: Dict with 'repos' key containing list of repo dicts

    Returns:
        Dict where keys are repo names and values contain 'plan_md' string

    Raises:
        CircularDependencyError: If circular dependency detected
        ContractMismatchError: If provides/requires don't match
    """
    repos = unified_architecture.get("repos", [])

    # Step 1: Build dependency graph
    graph = build_dependency_graph(repos)

    # Step 2: Check for cycles
    cycles = find_cycles(graph)
    if cycles:
        cycle_str = " -> ".join(cycles[0])
        raise CircularDependencyError(
            f"Circular dependency detected: {cycle_str}"
        )

    # Step 3: Validate contracts
    contract_errors = validate_contracts(repos)
    if contract_errors:
        raise ContractMismatchError(
            f"Contract mismatch: {'; '.join(contract_errors)}"
        )

    # Step 4: Generate per-repo plans
    result: dict[str, dict[str, Any]] = {}
    for repo in repos:
        plan_md = generate_plan_md(repo, repos)
        result[repo["name"]] = {
            "plan_md": plan_md,
        }

    return result
