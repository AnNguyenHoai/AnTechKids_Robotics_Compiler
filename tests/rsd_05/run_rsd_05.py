"""RSD-05 portable launch/bootstrap contract checks."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import runtime_bootstrap


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    original_cwd = Path.cwd()
    original_path = os.environ.get("PATH")

    # Source mode is non-invasive: it keeps the developer interpreter/PATH and
    # does not change the working directory.
    source_env = {"PATH": "HOST-PATH", "CUSTOM": "keep-me"}
    source_result = runtime_bootstrap.bootstrap_environment(source_env)
    check("source environment is preserved", source_result == source_env)
    check("source bootstrap does not change cwd", Path.cwd() == original_cwd)
    check("host PATH remains untouched", os.environ.get("PATH") == original_path)

    # Simulate both the frozen executable and PyInstaller's extracted bundle.
    old_frozen = getattr(sys, "frozen", None)
    old_executable = sys.executable
    old_meipass = getattr(sys, "_MEIPASS", None)
    app_dir = ROOT / "_rsd05_app"
    internal_dir = app_dir / "_internal"
    fake_exe = app_dir / "RoboStudio.exe"
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
        internal_dir.mkdir(parents=True, exist_ok=True)
        sys.frozen = True
        sys.executable = str(fake_exe)
        sys._MEIPASS = str(internal_dir)
        os.environ.pop("ROBOSTUDIO_HOME", None)

        context = runtime_bootstrap.bootstrap(apply=False)
        check("frozen application root is executable-owned", context.application_root == app_dir.resolve())
        check("frozen bundle root is PyInstaller-owned", context.bundle_root == internal_dir.resolve())
        check("frozen mode is detected", context.frozen is True)

        env = runtime_bootstrap.bootstrap_environment({"PATH": "HOST-PATH", "CUSTOM": "keep-me"})
        core = app_dir.resolve() / "runtime" / "platformio"
        check("frozen bootstrap pins PlatformIO core", env["PLATFORMIO_CORE_DIR"] == str(core))
        check("frozen bootstrap pins PlatformIO packages", env["PLATFORMIO_PACKAGES_DIR"] == str(core / "packages"))
        check("frozen bootstrap pins PlatformIO platforms", env["PLATFORMIO_PLATFORMS_DIR"] == str(core / "platforms"))
        check("frozen bootstrap disables upgrade checks", env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] == "true")
        check("frozen bootstrap disables ANSI output", env["PLATFORMIO_NO_ANSI"] == "true")
        check("frozen bootstrap preserves host PATH", env["PATH"] == "HOST-PATH")
        check("frozen bootstrap preserves unrelated environment", env["CUSTOM"] == "keep-me")
        check("frozen bootstrap declares packaged mode", env["ROBOSTUDIO_RUNTIME_MODE"] == "packaged")
        check("frozen bootstrap does not use cwd", env["ROBOSTUDIO_HOME"] == str(app_dir.resolve()))
    finally:
        if old_frozen is None:
            try:
                del sys.frozen
            except AttributeError:
                pass
        else:
            sys.frozen = old_frozen
        sys.executable = old_executable
        if old_meipass is None:
            try:
                del sys._MEIPASS
            except AttributeError:
                pass
        else:
            sys._MEIPASS = old_meipass
        os.environ.pop("ROBOSTUDIO_HOME", None)
        if app_dir.exists():
            import shutil
            shutil.rmtree(app_dir)

    print("RSD-05 portable launch/bootstrap checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
