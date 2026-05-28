from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "works" / "copilot-setup-statusline" / "scripts" / "install_statusline.sh"
HELPER_PATH = ROOT / "works" / "copilot-setup-statusline" / "scripts" / "windows_terminal_font.py"


def _load_helper_module():
    spec = importlib.util.spec_from_file_location("windows_terminal_font", HELPER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def test_windows_terminal_font_helper_applies_defaults_and_matching_wsl_profile(tmp_path: Path) -> None:
    helper = _load_helper_module()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "profiles": {
                    "defaults": {},
                    "list": [
                        {"name": "Ubuntu-26.04", "source": "Microsoft.WSL", "font": {"face": "Consolas"}},
                        {"name": "Other", "source": "Microsoft.WSL"},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    result = helper.apply_font(settings_path, "Ubuntu-26.04", "MesloLGM Nerd Font")

    updated = json.loads(settings_path.read_text(encoding="utf-8"))
    assert result["updated"] is True
    assert Path(result["backup_path"]).exists()
    assert updated["profiles"]["defaults"]["font"]["face"] == "MesloLGM Nerd Font"
    matching_profile = next(profile for profile in updated["profiles"]["list"] if profile["name"] == "Ubuntu-26.04")
    assert matching_profile["font"]["face"] == "MesloLGM Nerd Font"
    other_profile = next(profile for profile in updated["profiles"]["list"] if profile["name"] == "Other")
    assert "font" not in other_profile


def test_windows_terminal_font_helper_inspects_existing_nerd_font(tmp_path: Path) -> None:
    helper = _load_helper_module()
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "profiles": {
                    "defaults": {"font": {"face": "MesloLGM Nerd Font"}},
                    "list": [{"name": "Ubuntu-26.04", "source": "Microsoft.WSL"}],
                }
            }
        ),
        encoding="utf-8",
    )
    font_dir = tmp_path / "fonts"
    font_dir.mkdir()
    (font_dir / "MesloLGMNerdFont-Regular.ttf").write_text("", encoding="utf-8")

    result = helper.inspect_settings(settings_path, "Ubuntu-26.04", [font_dir])

    assert result["configured"] is True
    assert result["configured_origin"] == "profiles.defaults.font.face"
    assert result["configured_face"] == "MesloLGM Nerd Font"
    assert result["installed_faces"] == ["MesloLGM Nerd Font"]


def test_install_statusline_sh_installs_oh_my_posh_and_updates_windows_terminal_font(tmp_path: Path) -> None:
    home = tmp_path / "home"
    copilot_dir = home / ".copilot"
    bin_dir = tmp_path / "bin"
    font_dir = tmp_path / "windows-fonts"
    terminal_settings = tmp_path / "windows-terminal-settings.json"
    home.mkdir()
    bin_dir.mkdir()
    font_dir.mkdir()
    terminal_settings.write_text(
        json.dumps(
            {
                "profiles": {
                    "defaults": {},
                    "list": [
                        {"name": "Ubuntu-26.04", "source": "Microsoft.WSL", "font": {"face": "Consolas"}}
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    _write_executable(
        bin_dir / "curl",
        """#!/bin/sh
output=""
previous=""
for arg in "$@"; do
  if [ "$previous" = "-o" ]; then
    output="$arg"
  fi
  previous="$arg"
done
if [ -n "$output" ]; then
  cat >"$output" <<'EOF'
#!/bin/sh
if [ "$1" = "version" ]; then
  echo "24.0.0"
  exit 0
fi
exit 0
EOF
  chmod +x "$output"
  exit 0
fi
cat <<'EOF'
#!/bin/sh
set -eu
install_dir=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-d" ]; then
    shift
    install_dir="$1"
  fi
  shift || true
done
mkdir -p "$install_dir"
cat >"$install_dir/oh-my-posh" <<'EOS'
#!/bin/sh
if [ "$1" = "version" ]; then
  echo "24.0.0"
  exit 0
fi
exit 0
EOS
chmod +x "$install_dir/oh-my-posh"
EOF
""",
    )
    _write_executable(
        bin_dir / "oh-my-posh.exe",
        """#!/bin/sh
if [ "$1" = "font" ] && [ "$2" = "install" ] && [ "$3" = "meslo" ]; then
  touch "$HOST_FONT_DIR/MesloLGMNerdFont-Regular.ttf"
  exit 0
fi
exit 0
""",
    )

    env = dict(os.environ)
    env["HOME"] = str(home)
    env["PATH"] = f"{bin_dir}:{os.defpath}"
    env["COPILOT_STATUSLINE_FORCE_WSL"] = "1"
    env["WSL_DISTRO_NAME"] = "Ubuntu-26.04"
    env["COPILOT_STATUSLINE_WINDOWS_TERMINAL_SETTINGS"] = str(terminal_settings)
    env["COPILOT_STATUSLINE_WINDOWS_FONT_DIRS"] = str(font_dir)
    env["HOST_FONT_DIR"] = str(font_dir)

    completed = subprocess.run(
        ["bash", str(INSTALLER), str(copilot_dir)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (copilot_dir / "statusline.sh").exists()
    assert (copilot_dir / "statusline.omp.json").exists()
    assert (home / ".local" / "bin" / "oh-my-posh").exists()
    assert (font_dir / "MesloLGMNerdFont-Regular.ttf").exists()

    settings = json.loads((copilot_dir / "settings.json").read_text(encoding="utf-8"))
    assert settings["statusLine"]["command"] == str(copilot_dir / "statusline.sh")
    assert "STATUS_LINE" in settings["feature_flags"]["enabled"]

    terminal = json.loads(terminal_settings.read_text(encoding="utf-8"))
    assert terminal["profiles"]["defaults"]["font"]["face"] == "MesloLGM Nerd Font"
    assert terminal["profiles"]["list"][0]["font"]["face"] == "MesloLGM Nerd Font"
    assert list(tmp_path.glob("windows-terminal-settings.json.statusline-backup-*"))


def test_install_statusline_sh_falls_back_to_direct_binary_download_on_pure_linux(tmp_path: Path) -> None:
    home = tmp_path / "home"
    copilot_dir = home / ".copilot"
    bin_dir = tmp_path / "bin"
    home.mkdir()
    bin_dir.mkdir()

    _write_executable(
        bin_dir / "curl",
        """#!/bin/sh
output=""
url=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = "-o" ]; then
    shift
    output="$1"
  elif echo "$1" | grep -q 'https://cdn.ohmyposh.dev/releases/latest/posh-'; then
    url="$1"
  fi
  shift || true
done
case "$url" in
  *https://cdn.ohmyposh.dev/releases/latest/posh-*)
    cat >"$output" <<'EOF'
#!/bin/sh
if [ "$1" = "version" ]; then
  echo "29.14.0"
  exit 0
fi
exit 0
EOF
    chmod +x "$output"
    exit 0
    ;;
  *)
    exit 1
    ;;
esac
""",
    )

    env = dict(os.environ)
    env["HOME"] = str(home)
    env["PATH"] = f"{bin_dir}:{os.defpath}"
    env["SSH_CONNECTION"] = "client server"

    completed = subprocess.run(
        ["bash", str(INSTALLER), str(copilot_dir)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (home / ".local" / "bin" / "oh-my-posh").exists()
    assert "direct oh-my-posh binary fallback" in completed.stdout + completed.stderr
    assert "Linux/SSH note:" in completed.stdout

    settings = json.loads((copilot_dir / "settings.json").read_text(encoding="utf-8"))
    assert settings["statusLine"]["command"] == str(copilot_dir / "statusline.sh")
    assert "STATUS_LINE" in settings["feature_flags"]["enabled"]
