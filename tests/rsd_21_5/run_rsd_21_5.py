"""RSD-21.5 regression tests for production RoboStudio + Compiler E2E."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
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


def _make_production_distribution(base: Path) -> Path:
    executable = base / "RoboStudio.exe"
    executable.write_text(
        "import pathlib, sys\n"
        "args=sys.argv[1:]\n"
        "if '--self-test' in args:\n"
        " print('ROBOSTUDIO_E2E_READY')\n"
        " raise SystemExit(0)\n"
        "if '--compile' in args:\n"
        " output=pathlib.Path(args[args.index('--output')+1])\n"
        " output.parent.mkdir(parents=True, exist_ok=True)\n"
        " output.write_text('ROBOT_BYTECODE_E2E_OK\\n', encoding='utf-8')\n"
        " print('COMPILE_OK')\n"
        " raise SystemExit(0)\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    (base / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    resources = base / "resources"
    resources.mkdir(parents=True)
    (resources / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")
    runtime_resources.write_resource_manifest(resources)
    output = base / "distribution"
    production_distribution.build_production_distribution(
        production_distribution.ProductionDistributionInputs(
            executable=executable,
            runtime_resources=resources,
            version_file=base / "VERSION",
        ),
        output,
    )
    return output


def _build_release(distribution: Path, base: Path) -> Path:
    artifact = base / "release" / "RoboStudio-1.2.3-Windows.zip"
    release_package.build_release(distribution, artifact)
    release_provenance.write_provenance(
        distribution,
        artifact.with_name("release-manifest.json"),
        artifact,
        artifact.with_name(release_provenance.PROVENANCE_MANIFEST),
        source_revision="rsd-21-5-test-revision",
    )
    return artifact


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-5-test-") as temp:
        base = Path(temp)
        distribution = _make_production_distribution(base)
        artifact = _build_release(distribution, base)
        source = base / "sample.py"
        source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")

        result = production_e2e.qualify_release_e2e(
            artifact,
            source=source,
            launch_command=[sys.executable, "{app}", "--self-test"],
            compile_command=[sys.executable, "{app}", "--compile", "{source}", "--output", "{output}"],
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
