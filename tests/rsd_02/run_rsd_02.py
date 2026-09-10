from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        root.mkdir()

        with patch.dict(os.environ, {runtime_paths.APPLICATION_HOME_ENV: str(root)}, clear=False):
            check("application root ignores current working directory", runtime_paths.application_root() == root.resolve())
            check(
                "normal user data is outside application root",
                runtime_paths.user_data_root() != root.resolve(),
            )
            check(
                "portable data is explicitly opt-in",
                runtime_paths.user_data_root() != root.resolve() / "data",
            )

            with patch.dict(os.environ, {runtime_paths.PORTABLE_DATA_ENV: "1"}, clear=False):
                check(
                    "portable data resolves under application root",
                    runtime_paths.user_data_root() == root.resolve() / "data",
                )

            runtime_bin = root / "runtime" / "bin"
            runtime_bin.mkdir(parents=True)
            pio = runtime_bin / "pio.exe"
            pio.write_text("stub", encoding="utf-8")
            with patch.object(runtime_paths, "is_frozen", return_value=True):
                resolved = runtime_paths.resolve_bundled_tool("pio")
                check("bundled pio is discovered", resolved == pio)
                command = runtime_paths.platformio_command("run")
                check("packaged pio command uses absolute path", command == [str(pio), "run"])

            with patch.object(runtime_paths, "is_frozen", return_value=True):
                pio.unlink()
                try:
                    runtime_paths.platformio_command("run")
                except runtime_paths.RuntimePathError as exc:
                    check("frozen runtime rejects missing bundled pio", "runtime/bin/pio.exe" in str(exc))
                else:
                    raise AssertionError("frozen runtime unexpectedly used PATH/system Python")

            with patch.object(runtime_paths, "is_frozen", return_value=False):
                command = runtime_paths.platformio_command("run")
                check(
                    "source development keeps interpreter fallback",
                    command[:3] == [sys.executable, "-m", "platformio"],
                )

            with patch.dict(os.environ, {runtime_paths.APPLICATION_HOME_ENV: str(root)}, clear=False):
                source_path = runtime_paths.resolve_path("assets", "robot.json")
                check("resource path is rooted at application home", source_path == root / "assets" / "robot.json")
                data_path = runtime_paths.resolve_path("projects", writable=True)
                check("writable path is rooted at user data", data_path == runtime_paths.user_data_root() / "projects")

    print("RSD-02 runtime path checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
