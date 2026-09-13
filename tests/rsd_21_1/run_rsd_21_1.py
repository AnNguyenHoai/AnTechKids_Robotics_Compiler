"""RSD-21.1 production release boundary regression checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import release_boundary


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    items = release_boundary.boundary_items()
    check("boundary schema is stable", release_boundary.SCHEMA == "antechkids.robostudio.release-boundary")
    check("boundary schema version is stable", release_boundary.SCHEMA_VERSION == 1)
    check("RoboStudio is packaged", any(i.name == "RoboStudio" and i.package for i in items))
    check("Compiler is packaged", any(i.name == "Compiler" and i.package for i in items))
    check("application resources are packaged", any(i.name == "Application resources" and i.package for i in items))
    check(
        "application-local dependencies are packaged",
        any(i.name == "Application-local libraries and PE dependencies" and i.package for i in items),
    )
    check("Python is target prerequisite", any(i.name == "Python" and not i.package for i in release_boundary.target_prerequisites()))
    check("PlatformIO is target prerequisite", any(i.name == "PlatformIO" and not i.package for i in release_boundary.target_prerequisites()))
    check("ESP32 driver is target prerequisite", any(i.name == "ESP32/USB driver" and not i.package for i in release_boundary.target_prerequisites()))
    check("Git is not a release payload", any(i.name == "Git" and not i.package for i in items))
    check("source repository is developer-only", any(i.name == "Source repository" and not i.package for i in release_boundary.developer_only_items()))
    check("developer environment is developer-only", any(i.name == "Developer virtual environment" and not i.package for i in release_boundary.developer_only_items()))

    payload = release_boundary.to_dict()
    check("machine-readable contract is JSON serializable", json.dumps(payload))
    check("artifact model is RoboStudio + Compiler", payload["artifact_model"] == "RoboStudio + Compiler")
    check("packaged and target prerequisite sets are non-empty", bool(release_boundary.packaged_items()) and bool(release_boundary.target_prerequisites()))

    print("RSD-21.1 release boundary checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
