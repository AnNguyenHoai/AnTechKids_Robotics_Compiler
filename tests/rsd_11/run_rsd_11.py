"""RSD-11 portable PlatformIO build isolation contract tests."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build_isolation, runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except build_isolation.BuildIsolationError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def main() -> int:
    original_env = os.environ.copy()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp) / "User State Nguyễn An"
            source_root = Path(tmp) / "RoboStudio Source"
            source_root.mkdir()
            os.environ[runtime_paths.APPLICATION_HOME_ENV] = str(source_root)
            os.environ[runtime_paths.STATE_ROOT_ENV] = str(state_root)
            os.environ[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
            os.environ[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"
            os.environ["PLATFORMIO_WORKSPACE_DIR"] = "C:\\host\\workspace"
            os.environ["PLATFORMIO_BUILD_DIR"] = "C:\\host\\build"
            os.environ["PLATFORMIO_LIBDEPS_DIR"] = "C:\\host\\libdeps"

            workspace = build_isolation.build_workspace("lesson_001")
            check(
                "build workspace is outside application source",
                source_root not in workspace.parents and workspace != source_root,
            )
            check(
                "build workspace is under explicit user state",
                workspace
                == state_root.resolve() / "build" / "lesson_001" / "platformio",
            )
            check(
                "build workspace ignores host workspace override",
                workspace != Path(os.environ["PLATFORMIO_WORKSPACE_DIR"]),
            )

            second = build_isolation.build_workspace("lesson_002")
            check("projects receive isolated workspaces", second != workspace)
            check(
                "build directory is below isolated workspace",
                build_isolation.build_dir("lesson_001") == workspace / "build",
            )
            check(
                "library dependencies are isolated",
                build_isolation.libdeps_dir("lesson_001") == workspace / "libdeps",
            )
            check(
                "build cache is isolated",
                build_isolation.build_cache_dir("lesson_001")
                == workspace / "build-cache",
            )

            env = build_isolation.build_environment("lesson_001", os.environ)
            check(
                "workspace environment is absolute",
                Path(env["PLATFORMIO_WORKSPACE_DIR"]).is_absolute(),
            )
            check(
                "build directory environment is isolated",
                Path(env["PLATFORMIO_BUILD_DIR"])
                == build_isolation.build_dir("lesson_001"),
            )
            check(
                "libdeps environment is isolated",
                Path(env["PLATFORMIO_LIBDEPS_DIR"])
                == build_isolation.libdeps_dir("lesson_001"),
            )
            check(
                "registry cache is isolated",
                Path(env["PLATFORMIO_CACHE_DIR"])
                == build_isolation.cache_dir("lesson_001"),
            )
            check(
                "compiled cache is isolated",
                Path(env["PLATFORMIO_BUILD_CACHE_DIR"])
                == build_isolation.build_cache_dir("lesson_001"),
            )
            check(
                "host workspace override cannot leak",
                env["PLATFORMIO_WORKSPACE_DIR"] != "C:\\host\\workspace",
            )
            check(
                "host build override cannot leak",
                env["PLATFORMIO_BUILD_DIR"] != "C:\\host\\build",
            )

            prepared = build_isolation.prepare_build_workspace("lesson_001")
            check("isolated workspace can be prepared", prepared.is_dir())
            check("source tree remains clean", not (source_root / ".pio").exists())
            check("release-local data directory is absent", not (source_root / "data").exists())

            firmware = build_isolation.firmware_path("lesson_001", "esp32dev")
            check(
                "firmware resolves inside isolated build",
                firmware
                == build_isolation.build_dir("lesson_001")
                / "esp32dev"
                / "firmware.bin",
            )
            check("firmware path is outside source tree", source_root not in firmware.parents)

            expect_error(
                "path traversal project is rejected",
                lambda: build_isolation.build_workspace("../escape"),
                "single path component",
            )
            expect_error(
                "absolute project path is rejected",
                lambda: build_isolation.build_workspace(str(source_root)),
                "single path component",
            )
            expect_error(
                "reserved project name is rejected",
                lambda: build_isolation.build_workspace("CON"),
                "reserved",
            )
            expect_error(
                "unsafe environment name is rejected",
                lambda: build_isolation.firmware_path("lesson_001", "../esp32dev"),
                "Invalid PlatformIO environment",
            )

            build_isolation.clean_build_workspace("lesson_001")
            check("isolated workspace can be cleaned", not workspace.exists())

        deploy = (ROOT / "tools" / "deploy_robot.py").read_text(encoding="utf-8")
        check(
            "deployment uses build isolation",
            "build_isolation.prepare_build_workspace(project_name)" in deploy,
        )
        check(
            "deployment injects isolated PlatformIO environment",
            "project_name=project_name" in deploy,
        )
        check(
            "deployment does not hardcode PlatformIO .pio output",
            'PLATFORM / ".pio"' not in deploy,
        )
        check(
            "OTA artifact uses isolated firmware resolver",
            "build_isolation.firmware_path" in deploy,
        )
    finally:
        os.environ.clear()
        os.environ.update(original_env)

    print("RSD-11 portable build isolation checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
