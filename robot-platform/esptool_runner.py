#!/usr/bin/env python3
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def _candidate_package_roots() -> list[Path]:
    roots: list[Path] = []

    explicit = os.environ.get("PLATFORMIO_PACKAGES_DIR", "").strip()
    if explicit:
        roots.append(Path(explicit).expanduser())

    core = os.environ.get("PLATFORMIO_CORE_DIR", "").strip()
    if core:
        roots.append(Path(core).expanduser() / "packages")

    # Normal developer PlatformIO fallback. Production RoboStudio always pins
    # one of the explicit locations above, but keeping this fallback means the
    # firmware source remains buildable in ordinary local PlatformIO setups.
    roots.append(Path.home() / ".platformio" / "packages")
    return roots


def _resolve_esptool_root() -> Path:
    checked: list[str] = []
    for packages in _candidate_package_roots():
        tool_root = packages.resolve() / "tool-esptoolpy"
        checked.append(str(tool_root))
        if (tool_root / "esptool.py").is_file() and (tool_root / "esptool").is_dir():
            return tool_root
    raise RuntimeError(
        "Unable to locate PlatformIO tool-esptoolpy package. Checked: "
        + ", ".join(checked)
    )


def main() -> None:
    tool_root = _resolve_esptool_root()
    contrib = tool_root / "_contrib"

    # python310._pth intentionally isolates RoboStudio's embedded interpreter.
    # External scripts therefore do not receive their own directory on
    # sys.path. Add only the PlatformIO-owned esptool roots required by this
    # command instead of disabling isolation globally.
    for path in (contrib, tool_root):
        if path.is_dir():
            value = str(path)
            if value not in sys.path:
                sys.path.insert(0, value)

    script = tool_root / "esptool.py"
    sys.argv[0] = str(script)
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
