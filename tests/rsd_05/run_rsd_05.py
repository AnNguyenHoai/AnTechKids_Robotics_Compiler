"""RSD-05 portable launch/bootstrap contract checks."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import runtime_bootstrap, runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    original_cwd = Path.cwd()
    original_path = os.environ.get("PATH")
    original_env = os.environ.copy()

    source_env = {"PATH": "HOST-PATH", "CUSTOM": "keep-me"}
    source_result = runtime_bootstrap.bootstrap_environment(source_env)
    check("source environment is preserved", source_result == source_env)
    check("source bootstrap does not change cwd", Path.cwd() == original_cwd)
    check("host PATH remains untouched", os.environ.get("PATH") == original_path)

    old_frozen = getattr(sys, "frozen", None)
    old_executable = sys.executable
    old_meipass = getattr(sys, "_MEIPASS", None)
    app_dir = ROOT / "_rsd05_app"
    state_dir = ROOT / "_rsd05_state"
    internal_dir = app_dir / "_internal"
    fake_exe = app_dir / "RoboStudio.exe"
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
        internal_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "runtime" / "bin").mkdir(parents=True, exist_ok=True)
        (app_dir / "runtime" / "platformio" / "platforms").mkdir(parents=True, exist_ok=True)
        (app_dir / "runtime" / "platformio" / "packages").mkdir(parents=True, exist_ok=True)
        sys.frozen = True
        sys.executable = str(fake_exe)
        sys._MEIPASS = str(internal_dir)
        os.environ.pop("ROBOSTUDIO_HOME", None)
        os.environ[runtime_paths.STATE_ROOT_ENV] = str(state_dir)

        context = runtime_bootstrap.bootstrap(apply=False)
        check("frozen application root is executable-owned", context.application_root == app_dir.resolve())
        check("frozen bundle root is PyInstaller-owned", context.bundle_root == internal_dir.resolve())
        check("frozen mode is detected", context.frozen is True)
        check("frozen user state is external", context.user_data_root == state_dir.resolve())
        check("inspection does not create state", not state_dir.exists())

        env = runtime_bootstrap.bootstrap_environment({
            "PATH": "HOST-PATH",
            "CUSTOM": "keep-me",
            "NODE_PATH": "HOST-NODE",
            runtime_paths.STATE_ROOT_ENV: str(state_dir),
        })
        packaged = app_dir.resolve() / "runtime" / "platformio"
        mutable_core = state_dir.resolve() / "platformio" / "core"
        check("frozen bootstrap moves PlatformIO core state outside artifact", Path(env["PLATFORMIO_CORE_DIR"]).resolve() == mutable_core)
        check("frozen bootstrap pins PlatformIO packages", Path(env["PLATFORMIO_PACKAGES_DIR"]).resolve() == (packaged / "packages").resolve())
        check("frozen bootstrap pins PlatformIO platforms", Path(env["PLATFORMIO_PLATFORMS_DIR"]).resolve() == (packaged / "platforms").resolve())
        check("frozen bootstrap pins external state root", Path(env[runtime_paths.STATE_ROOT_ENV]).resolve() == state_dir.resolve())
        check("frozen bootstrap disables upgrade checks", env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] == "true")
        check("frozen bootstrap disables ANSI output", env["PLATFORMIO_NO_ANSI"] == "true")
        check("frozen bootstrap disables Python user site", env["PYTHONNOUSERSITE"] == "1")
        check("frozen bootstrap disables Python bytecode writes", env["PYTHONDONTWRITEBYTECODE"] == "1")
        check("frozen bootstrap closes host PATH", env["PATH"] != "HOST-PATH")
        check("frozen bootstrap removes host Node injection", "NODE_PATH" not in env)
        check("frozen bootstrap preserves unrelated environment", env["CUSTOM"] == "keep-me")
        check("frozen bootstrap declares packaged mode", env["ROBOSTUDIO_RUNTIME_MODE"] == "packaged")
        check("frozen bootstrap declares dependency closure", env["ROBOSTUDIO_DEPENDENCY_MODE"] == "artifact-closed")
        check("frozen bootstrap does not use cwd", Path(env["ROBOSTUDIO_HOME"]).resolve() == app_dir.resolve())
    finally:
        os.environ.clear()
        os.environ.update(original_env)
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
        import shutil
        if app_dir.exists():
            shutil.rmtree(app_dir)
        if state_dir.exists():
            shutil.rmtree(state_dir)

    print("RSD-05 portable launch/bootstrap checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
