from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import runtime_resources
from tools.package_runtime_resources import package_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, text: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        check(name, text in str(exc))
    else:
        raise AssertionError(f"{name}: expected RuntimeError")


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        app = temp_root / "RoboStudio"
        source = temp_root / "packages"
        source_resource = source / "robot-isa" / "target_profiles.json"
        source_resource.parent.mkdir(parents=True)
        source_resource.write_text(
            json.dumps({"schema_version": 1, "kind": "robot_target_capability_profiles", "profiles": []}),
            encoding="utf-8",
        )

        packaged = app / "runtime" / "resources"
        result = package_resources(source, packaged)
        check("resource package is created", packaged.is_dir())
        check("declared resource is copied", (packaged / "robot-isa" / "target_profiles.json").is_file())
        check("resource manifest is written", Path(result["manifest"]).is_file())

        with patch.dict(os.environ, {runtime_resources.APPLICATION_HOME_ENV: str(app)}, clear=False):
            with patch.object(runtime_resources, "is_frozen", return_value=True):
                resolved = runtime_resources.resolve_resource("target_profiles")
                check(
                    "frozen resource resolves under application-owned runtime",
                    resolved == packaged / "robot-isa" / "target_profiles.json",
                )
                check(
                    "resource manifest validates",
                    runtime_resources.validate_resource_manifest()["schema_version"] == 1,
                )

                outside = temp_root / "outside.json"
                outside.write_text("{}", encoding="utf-8")
                expect_error(
                    "unknown resource cannot escape registry",
                    lambda: runtime_resources.resolve_resource("../../outside"),
                    "Unknown RoboStudio runtime resource",
                )

                (packaged / "robot-isa" / "target_profiles.json").write_text("tampered", encoding="utf-8")
                expect_error(
                    "resource checksum drift is rejected",
                    runtime_resources.validate_resource_manifest,
                    "checksum mismatch",
                )

        with patch.object(runtime_resources, "is_frozen", return_value=False):
            with patch.dict(os.environ, {runtime_resources.APPLICATION_HOME_ENV: ""}, clear=False):
                resolved = runtime_resources.resolve_resource("target_profiles")
                check(
                    "source development keeps repository resource fallback",
                    resolved == ROOT / "packages" / "robot-isa" / "target_profiles.json",
                )

        with patch.dict(os.environ, {runtime_resources.APPLICATION_HOME_ENV: str(app)}, clear=False):
            with patch.object(runtime_resources, "is_frozen", return_value=True):
                (packaged / "robot-isa" / "target_profiles.json").unlink()
                expect_error(
                    "frozen runtime rejects missing resource",
                    lambda: runtime_resources.resolve_resource("target_profiles"),
                    "Required packaged RoboStudio runtime resource is missing",
                )

    print("RSD-03 runtime resource packaging checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
