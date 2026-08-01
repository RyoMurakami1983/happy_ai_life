from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECRET_GUARD = ROOT / "repo-template" / ".githooks" / "lib" / "secret-guard.sh"


def _resolve_posix_shell() -> str:
    env_shell = os.environ.get("SECRET_GUARD_SHELL")
    if env_shell:
        return env_shell

    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        for base in (Path(program_files), Path(program_files_x86)):
            for candidate in (
                base / "Git" / "bin" / "bash.exe",
                base / "Git" / "usr" / "bin" / "sh.exe",
                base / "Git" / "bin" / "sh.exe",
            ):
                if candidate.exists():
                    return str(candidate)

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    system32 = Path(system_root) / "System32"
    for candidate in ("bash", "sh"):
        resolved = shutil.which(candidate)
        if not resolved:
            continue
        resolved_path = Path(resolved)
        if os.name == "nt" and resolved_path.resolve().is_relative_to(system32.resolve()):
            continue
        return resolved

    raise RuntimeError("No POSIX shell was found for the secret guard compatibility tests.")


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return completed.stdout.strip()


def _write_gitleaks_shim(bin_dir: Path, *, mode: str) -> Path:
    shim = bin_dir / "gitleaks"
    shim.write_text(
        f"""#!/usr/bin/env sh
set -eu
log_file="${{GITLEAKS_LOG_FILE:?}}"
scan_exit="${{GITLEAKS_SCAN_EXIT_CODE:-0}}"
scan_output="${{GITLEAKS_SCAN_OUTPUT:-}}"
printf '%s\\n' "$*" >> "$log_file"
case "${{1:-}}" in
  detect)
    if [ "${{2:-}}" = "--help" ]; then
      [ "{mode}" = "detect" ] && exit 0
      exit 2
    fi
    if [ "{mode}" = "detect" ]; then
      [ -z "$scan_output" ] || printf '%s\\n' "$scan_output" >&2
      exit "$scan_exit"
    fi
    exit 2
    ;;
  dir|git)
    if [ "${{2:-}}" = "--help" ]; then
      [ "{mode}" = "legacy" ] && exit 0
      exit 2
    fi
    if [ "{mode}" = "legacy" ]; then
      [ -z "$scan_output" ] || printf '%s\\n' "$scan_output" >&2
      exit "$scan_exit"
    fi
    exit 2
    ;;
  *)
    exit 2
    ;;
esac
""",
        encoding="utf-8",
    )
    shim.chmod(0o755)
    return shim


def _tool_env(
    tmp_path: Path,
    *,
    mode: str,
    log_file: Path,
    scan_exit_code: int = 0,
    scan_output: str = "",
) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shim = _write_gitleaks_shim(bin_dir, mode=mode)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["GITLEAKS_BIN"] = str(shim)
    env["GITLEAKS_LOG_FILE"] = str(log_file)
    env["GITLEAKS_SCAN_EXIT_CODE"] = str(scan_exit_code)
    env["GITLEAKS_SCAN_OUTPUT"] = scan_output
    return env


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Copilot")
    _git(repo, "config", "user.email", "copilot@example.com")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "base")


class SecretGuardGitleaksCompatTests(unittest.TestCase):
    def _run_secret_guard(
        self,
        tmp_path: Path,
        *,
        mode: str,
        args: list[str] | None = None,
        staged_change: bool = False,
        scan_exit_code: int = 0,
        scan_output: str = "",
    ) -> tuple[subprocess.CompletedProcess[str], list[str]]:
        repo = tmp_path / "repo"
        _init_repo(repo)
        if staged_change:
            (repo / "tracked.txt").write_text("changed\n", encoding="utf-8")
            _git(repo, "add", "tracked.txt")

        log_file = tmp_path / "gitleaks.log"
        env = _tool_env(
            tmp_path,
            mode=mode,
            log_file=log_file,
            scan_exit_code=scan_exit_code,
            scan_output=scan_output,
        )
        command = [_resolve_posix_shell(), str(SECRET_GUARD), *(args or [])]
        completed = subprocess.run(
            command,
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        lines = log_file.read_text(encoding="utf-8").splitlines()
        return completed, lines

    def test_secret_guard_uses_detect_for_staged_scan_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            completed, lines = self._run_secret_guard(tmp_path, mode="detect", staged_change=True)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("detect --help", lines[0])
            self.assertTrue(any(line.startswith("detect --source ") and "--no-git" in line for line in lines))
            self.assertFalse(any(line.startswith("dir ") for line in lines))

    def test_secret_guard_falls_back_to_legacy_git_scan_for_range(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            completed, lines = self._run_secret_guard(
                tmp_path,
                mode="legacy",
                args=["--range", "HEAD~1..HEAD"],
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("detect --help", lines[0])
            self.assertIn("dir --help", lines[1])
            self.assertIn("git --help", lines[2])
            self.assertTrue(any(line.startswith("git ") and "--log-opts HEAD~1..HEAD" in line for line in lines))
            self.assertFalse(
                any(line.startswith("detect --source ") and "--log-opts HEAD~1..HEAD" in line for line in lines)
            )

    def test_secret_guard_reports_secret_detection_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            completed, _ = self._run_secret_guard(
                tmp_path,
                mode="detect",
                staged_change=True,
                scan_exit_code=1,
                scan_output="detected secret details",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Potential secrets were detected in staged changes.", completed.stderr)
            self.assertIn("detected secret details", completed.stderr)

    def test_secret_guard_reports_gitleaks_runtime_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            completed, _ = self._run_secret_guard(
                tmp_path,
                mode="detect",
                staged_change=True,
                scan_exit_code=2,
                scan_output="runtime failure details",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Failed to run gitleaks for the staged secret scan.", completed.stderr)
            self.assertIn("runtime failure details", completed.stderr)


if __name__ == "__main__":
    unittest.main()
