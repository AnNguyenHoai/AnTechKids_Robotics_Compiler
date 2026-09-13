"""RSD-21.5 regression tests for the production E2E runner."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.rsd_20_p.run_rsd_20_p import _build_release, _make_distribution
from tools import production_e2e, release_provenance


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _application_script(base: Path) -> Path:
    script = base / "robostudio_test_app.py"
    script.write_text(
        "import pathlib, sys\n"
        "args=sys.argv[1:]\n"
        "if '--self-test' in args:\n"
        " print('ROBOSTUDIO_E2E_READY')\n"
        " raise SystemExit(0)\n"
        "if '--compile' in args:\n"
        " source=pathlib.Path(args[args.index('--compile')+1])\n"
        " output=pathlib.Path(args[args.index('--output')+1])\n"
        " output.parent.mkdir(parents=True, exist_ok=True)\n"
        " output.write_text('BYTECODE_FROM_PRODUCTION_APP\\n', encoding='utf-8')\n"
        " print('COMPILE_OK')\n"
        " raise SystemExit(0)\n"
        "raise SystemExit(2)\n",
        encoding="utf-8",
    )
    return script


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-5-test-") as temp:
        base = Path(temp)
        distribution = _make_distribution(base / "distribution", imported_dll="Qt6Core.dll")
        # The existing release fixture needs a single application filename.
        app = _application_script(base)
        executable = distribution / "RoboStudio.exe"
        executable.write_text(app.read_text(encoding="utf-8"), encoding="utf-8")
        artifact = _build_release(distribution, base, "RoboStudio-1.2.3-Windows")
        provenance = artifact.with_name(release_provenance.PROVENANCE_MANIFEST)
        release_provenance.write_provenance(distribution, artifact.with_name("release-manifest.json"), artifact, provenance, source_revision="rsd-21-5-test")

        source = base / "sample.py"
        source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")
        output = base / "expected-bytecode" / "program.bytecode"
        launch = [sys.executable, "{app}", "--self-test"]
        compile_command = [sys.executable, "{app}", "--compile", "{source}", "--output", "{output}"]

        result = production_e2e.qualify_release_e2e(
            artifact,
            source=source,
            launch_command=launch,
            compile_command=compile_command,
        )
        report = production_e2e.build_report(result)

        check("E2E schema is stable", report["schema"] == "antechkids.robostudio.production-e2e")
        check("E2E schema version is stable", report["schema_version"] == 1)
        check("production artifact is the system under test", report["artifact"] == artifact.name)
        check("RoboStudio starts from extracted release", report["robostudio"]["started"] is True)
        check("RoboStudio startup marker is captured", "ROBOSTUDIO_E2E_READY" in report["robostudio"]["stdout"])
        check("Compiler executes through application command", report["compiler"]["executed"] is True)
        check("Compiler output is produced", report["compiler"]["output_produced"] is True)
        check("E2E result is PASS", report["status"] == "PASS")
        check("E2E is target-machine scoped", report["target_machine"] is True)
        check("host prerequisites remain external", report["host_prerequisites_packaged"] is False)
        check("E2E report is JSON serializable", bool(json.dumps(report)))

    print("RSD-21.5 RoboStudio + Compiler E2E checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
