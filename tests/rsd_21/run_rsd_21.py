"""RSD-21 production release qualification contract tests."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.rsd_20_p.run_rsd_20_p import _build_release, _make_distribution
from tools import production_release_qualification, release_provenance, target_machine_qualification


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def capture(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO(); stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = production_release_qualification.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def _build_qualified_release(distribution: Path, base: Path, name: str) -> tuple[Path, Path]:
    artifact = _build_release(distribution, base, name)
    manifest = artifact.with_name("release-manifest.json")
    provenance = artifact.with_name(release_provenance.PROVENANCE_MANIFEST)
    release_provenance.write_provenance(distribution, manifest, artifact, provenance, source_revision="rsd-21-test-revision")
    return artifact, provenance


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd21-") as temp:
        base = Path(temp)
        distribution = _make_distribution(base / "distribution", imported_dll="Qt6Core.dll")
        artifact, provenance = _build_qualified_release(distribution, base, "RoboStudio-1.2.3-Windows")
        report = base / "qualification.json"
        code, stdout, stderr = capture([str(artifact), "--provenance", str(provenance), "--report", str(report)])
        check("qualification command succeeds", code == 0)
        check("qualification reports PASS", "RSD-21 production release qualification: PASS" in stdout)
        check("qualification failure text is empty", not stderr)
        check("qualification report exists", report.is_file())
        payload = json.loads(report.read_text(encoding="utf-8"))
        check("qualification schema is stable", payload["schema"] == "antechkids.robostudio.production-release-qualification")
        check("qualification status is PASS", payload["status"] == "PASS")
        check("qualification is marked qualified", payload["qualified"] is True)
        check("portable dependency closure is verified", payload["portable_dependency_closure"]["passed"] is True)
        check("provenance checksum is verified", payload["provenance"]["artifact_sha256_verified"] is True)
        check("deterministic ZIP is verified", payload["provenance"]["deterministic_zip_verified"] is True)
        check("acceptance is not claimed when not run", payload["acceptance"]["performed"] is False)

        acceptance_report = base / "target-machine-acceptance.json"
        qualified_report = base / "qualification-target-machine.json"
        code, stdout, stderr = capture([
            str(artifact), "--provenance", str(provenance), "--target-machine",
            "--prerequisite-scope", target_machine_qualification.target_machine_prerequisites.RequirementScope.COMPILE.value,
            "--acceptance-report", str(acceptance_report), "--report", str(qualified_report),
        ])
        check("qualification with target-machine prerequisites succeeds", code == 0)
        check("target-machine qualification reports PASS", "RSD-21 production release qualification: PASS" in stdout)
        check("target-machine qualification failure text is empty", not stderr)
        check("target-machine evidence exists", acceptance_report.is_file())
        target_payload = json.loads(acceptance_report.read_text(encoding="utf-8"))
        check("target-machine evidence is machine-readable", target_payload["schema"] == target_machine_qualification.SCHEMA)
        check("target-machine evidence is PASS", target_payload["passed"] is True)
        qualified_payload = json.loads(qualified_report.read_text(encoding="utf-8"))
        check("qualification records target-machine validation", qualified_payload["target_machine"]["performed"] is True)
        check("qualification does not claim bundled acceptance", qualified_payload["acceptance"]["performed"] is False)

        manifest_path = artifact.with_name("release-manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        check("release manifest sidecar exists", manifest_path.is_file())
        check("release manifest is machine-readable", isinstance(manifest, dict))
        tampered = base / "tampered-provenance.json"
        provenance_payload = json.loads(provenance.read_text(encoding="utf-8"))
        # source_revision is descriptive provenance metadata and is not
        # independently authenticated by the current sidecar contract. Tamper
        # with an integrity-bound field instead so this test proves the actual
        # validation guarantee rather than an unenforceable assumption.
        provenance_payload["artifact_sha256"] = "0" * 64
        tampered.write_text(json.dumps(provenance_payload, indent=2) + "\n", encoding="utf-8")
        code, _, _ = capture([str(artifact), "--provenance", str(tampered)])
        check("tampered provenance is rejected", code != 0)
    print("RSD-21 production release qualification checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
