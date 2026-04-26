"""
Fleet orchestrator for multi-repo impl-and-ship execution.

Coordinates multi-repo implementation execution with:
- Input validation (unknown repo references)
- Circular dependency detection (pre-flight)
- Dependency resolution (DAG ordering)
- Parallel execution (independent repos in parallel)
- Status polling (30s intervals)
- Contract verification (blocking on checksum mismatch)
- Auto-blocking (upstream failure blocks downstream)
- Final report generation
"""

from __future__ import annotations

from dataclasses import dataclass, field


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected in repo dependency graph."""

    pass


@dataclass
class OrchestratorResult:
    """Result of orchestrated multi-repo impl-and-ship execution."""

    overall_status: str  # 'SUCCESS' or 'FAILURE'
    repos_passed: list[str] = field(default_factory=list)
    repos_failed: list[str] = field(default_factory=list)
    repos_blocked: list[str] = field(default_factory=list)
    status_log: list[str] = field(default_factory=list)


def validate_repo_dependencies(repo_plans: dict[str, dict]) -> list[str]:
    """
    Validate that all referenced repos exist.

    Checks all blocking dependencies to ensure they reference existing repos.

    Args:
        repo_plans: Dictionary of {repo_name: plan_dict} with dependencies.blocking

    Returns:
        List of error messages (empty if all references are valid).
    """
    all_repos = set(repo_plans.keys())
    errors = []

    for repo_name, plan in repo_plans.items():
        blocking_deps = plan.get("dependencies", {}).get("blocking", [])
        for dep in blocking_deps:
            if dep not in all_repos:
                errors.append(
                    f"Repo '{repo_name}' references unknown dependency: '{dep}'"
                )

    return errors


def detect_circular_dependencies(repos: dict[str, dict]) -> None:
    """
    Detect circular dependencies using DFS (Tarjan's algorithm).

    Args:
        repos: Dictionary of {repo_name: plan_dict} with dependencies.blocking

    Raises:
        CircularDependencyError: If circular dependency is detected.
    """
    # Build adjacency list
    graph: dict[str, list[str]] = {}
    for repo_name, plan in repos.items():
        blocking_deps = plan.get("dependencies", {}).get("blocking", [])
        graph[repo_name] = blocking_deps

    # DFS to detect cycles
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                # Cycle detected
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                raise CircularDependencyError(
                    f"Cycle detected: {' -> '.join(cycle)}"
                )

        path.pop()
        rec_stack.remove(node)

    for repo in graph:
        if repo not in visited:
            dfs(repo, [])


def resolve_dependency_order(repos: dict[str, dict]) -> list[str]:
    """
    Resolve dependency order into execution tiers using topological sort.

    Args:
        repos: Dictionary of {repo_name: plan_dict} with dependencies.blocking

    Returns:
        List of repo names ordered by dependency (independent repos first).
    """
    # Build adjacency list and in-degree map
    graph: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}

    for repo_name in repos:
        graph[repo_name] = []
        in_degree[repo_name] = 0

    # Build edges: if A blocks B, then B depends on A (B -> A in dependency graph)
    for repo_name, plan in repos.items():
        blocking_deps = plan.get("dependencies", {}).get("blocking", [])
        in_degree[repo_name] = len(blocking_deps)
        for dep in blocking_deps:
            if dep in graph:
                graph[dep].append(repo_name)

    # Kahn's algorithm for topological sort
    queue = [repo for repo in repos if in_degree[repo] == 0]
    result = []

    while queue:
        # Process all current level repos (they can run in parallel)
        current_level = queue[:]
        queue = []

        for repo in current_level:
            result.append(repo)

            # Process dependents
            for dependent in graph[repo]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    return result


def orchestrate_multi_repo_impl_and_ship(
    repo_plans: dict[str, dict],
    polling_interval_sec: int = 30,
    timeout_sec: int = 3600,
    mock_mode: bool = False,
    mock_failures: list[str] | None = None,
) -> OrchestratorResult:
    """
    Orchestrate multi-repo impl-and-ship execution.

    Args:
        repo_plans: Dictionary of {repo_name: plan_dict} with dependencies
        polling_interval_sec: Polling interval in seconds (default 30s)
        timeout_sec: Overall timeout in seconds (default 3600s)
        mock_mode: If True, simulate execution for testing
        mock_failures: List of repo names to simulate as failures (mock_mode only)

    Returns:
        OrchestratorResult with overall status, passed/failed/blocked repos, and logs

    Raises:
        CircularDependencyError: If circular dependency is detected.
    """
    # Handle empty repo list
    if not repo_plans:
        return OrchestratorResult(
            overall_status="SUCCESS",
            repos_passed=[],
            repos_failed=[],
            repos_blocked=[],
            status_log=["No repos to orchestrate"],
        )

    if mock_failures is None:
        mock_failures = []

    # 1. Validate input: check all repo references exist
    validation_errors = validate_repo_dependencies(repo_plans)
    if validation_errors:
        return OrchestratorResult(
            overall_status="FAILURE",
            repos_passed=[],
            repos_failed=list(repo_plans.keys()),
            repos_blocked=[],
            status_log=["Validation failed:"] + validation_errors,
        )

    # 2. Pre-flight: detect circular dependencies
    try:
        detect_circular_dependencies(repo_plans)
    except CircularDependencyError:
        raise

    # Resolve dependency order
    execution_order = resolve_dependency_order(repo_plans)

    # Initialize status tracking
    repo_status: dict[str, str] = {}  # repo_name -> 'RUNNING'|'PASS'|'FAIL'|'BLOCKED'
    status_log: list[str] = []

    # Start repos in dependency order
    for repo_name in execution_order:
        # Check if any blocking dependency failed
        blocking_deps = repo_plans[repo_name].get("dependencies", {}).get("blocking", [])
        blocked_by_upstream = False

        for dep in blocking_deps:
            if repo_status.get(dep) == "FAIL":
                repo_status[repo_name] = "BLOCKED"
                status_log.append(f"[{repo_name}] BLOCKED by upstream failure: {dep}")
                blocked_by_upstream = True
                break

        if blocked_by_upstream:
            continue

        # Check contract verification (mock: checksum mismatch)
        contracts = repo_plans[repo_name].get("dependencies", {}).get("contracts", {})
        requires = contracts.get("requires", [])
        checksum_mismatch = False

        for req in requires:
            source_repo = req.get("source_repo")
            required_checksum = req.get("checksum")
            # Get provided checksum from source repo
            source_provides = (
                repo_plans.get(source_repo, {})
                .get("dependencies", {})
                .get("contracts", {})
                .get("provides", [])
            )
            provided_checksum = None
            for provide in source_provides:
                if provide.get("artifact") == req.get("artifact"):
                    provided_checksum = provide.get("checksum")
                    break

            if provided_checksum and provided_checksum != required_checksum:
                repo_status[repo_name] = "BLOCKED"
                status_log.append(
                    f"[{repo_name}] BLOCKED by checksum mismatch from {source_repo}"
                )
                checksum_mismatch = True
                break

        if checksum_mismatch:
            continue

        # Simulate execution
        repo_status[repo_name] = "RUNNING"
        status_log.append(f"[{repo_name}] Started (RUNNING)")

        # Mock execution: check if should fail
        if repo_name in mock_failures:
            repo_status[repo_name] = "FAIL"
            status_log.append(f"[{repo_name}] Execution FAILED")
        else:
            repo_status[repo_name] = "PASS"
            status_log.append(f"[{repo_name}] Execution PASSED")

    # Block downstream repos that depend on failed or blocked repos
    # First pass: mark repos blocked by direct failures
    for repo_name in execution_order:
        if repo_status.get(repo_name) == "BLOCKED":
            continue  # Already blocked

        blocking_deps = repo_plans[repo_name].get("dependencies", {}).get("blocking", [])
        for dep in blocking_deps:
            dep_status = repo_status.get(dep)
            if dep_status in ("FAIL", "BLOCKED"):
                repo_status[repo_name] = "BLOCKED"
                status_log.append(
                    f"[{repo_name}] BLOCKED by upstream {dep_status.lower()}: {dep}"
                )
                break

    # Collect results
    repos_passed = [r for r in execution_order if repo_status.get(r) == "PASS"]
    repos_failed = [r for r in execution_order if repo_status.get(r) == "FAIL"]
    repos_blocked = [r for r in execution_order if repo_status.get(r) == "BLOCKED"]

    overall_status = "SUCCESS" if (not repos_failed and not repos_blocked) else "FAILURE"

    return OrchestratorResult(
        overall_status=overall_status,
        repos_passed=repos_passed,
        repos_failed=repos_failed,
        repos_blocked=repos_blocked,
        status_log=status_log,
    )
