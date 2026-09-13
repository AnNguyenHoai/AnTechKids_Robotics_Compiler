"""RSD-21.5 production artifact E2E contract regression suite."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

# This test is intentionally executable directly from the repository root:
#   python tests\\rsd_21_5\\run_rsd_21_5.py
# Python puts tests/rsd_21_5 on sys.path for that invocation, not the repository
# root. Add the repository root before importing project packages.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_e2e, production_distribution, release_package, release_provenance, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-5-test-") as td:
        root = Path(td)
        artifact = root / "production.zip"
        source = root / "sample.py"
        source.write_text("print('robosim e2e')\n", encoding="utf-8")
        result = production_e2e.evaluate_production_artifact(
            artifact=artifact, source=source, launch=False
        )
        report = production_e2e.build_report(result)
        check("E2E schema is stable", report["schema"] == "antechkids.robostudio.production-e2e")
        check("E2E schema version is stable", report["schema_version"] == 1)
        check("production artifact is the system under test", report["artifact"] == artifact.name)
        check("RoboStudio starts from extracted release", report["robostudio"]["started"] is True)
        check("RoboStudio startup marker is captured", "ROBOSTUDIO_E2E_READY" in report["robostudio"]["stdout"])
        check("Compiler executes through packaged application", report["compiler"]["executed"] is True)
        check("Compiler output is produced", report["compiler"]["output_produced"] is True)
        check("E2E result is PASS", report["status"] == "PASS")
        check("E2E is target-machine scoped", report["target_machine"] is True)
        check("host prerequisites remain external", report["host_prerequisites_packaged"] is False)
        check("E2E report is JSON serializable", bool(json.dumps(report)))

        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("production ZIP contains RoboStudio", "RoboStudio.exe" in names)
        check("production ZIP contains compiler resources", any(name.startswith("runtime/resources/") for name in names))
        check("production ZIP does not contain Python", not any("python" in name.lower() for name in names))
        check("production ZIP does not contain PlatformIO", not any("platformio" in name.lower() for name in names))

    print("RSD-21.5 RoboStudio + Compiler E2E checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
