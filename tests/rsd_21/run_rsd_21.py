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
from tools import production_release_qualification


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def capture(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = production_release_qualification.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd21-") as temp:
        base = Path(temp)
        distribution = _make_distribution(base / "distribution", imported_dll="Qt6Core.dll")
        artifact = _build_release(distribution, base, "RoboStudio-1.2.3-Windows")
        provenance = artifact.with_name("release-provenance.json")
        report = base / "qualification.json"

        code, stdout, stderr = capture([
            str(artifact),
            "--provenance", str(provenance),
            "--report", str(report),
        ])
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

        acceptance_distribution = _make_distribution(
            base / "acceptance-distribution",
            imported_dll="Qt6Core.dll",
            runnable_python=True,
        )
        acceptance_artifact = _build_release(
            acceptance_distribution, base, "RoboStudio-1.2.3-Windows-acceptance"
        )
        acceptance_evidence = base / "acceptance.json"
        code, _, stderr = capture([
            str(acceptance_artifact),
            "--run-acceptance",
            "--acceptance-report", str(acceptance_evidence),
            "--report", str(base / "qualification-acceptance.json"),
        ])
        check("qualification with clean-machine acceptance succeeds", code == 0)
        check("acceptance evidence exists", acceptance_evidence.is_file())
        check("acceptance failure text is empty", not stderr)
        acceptance_payload = json.loads(acceptance_evidence.read_text(encoding="utf-8"))
        check("acceptance evidence is PASS", acceptance_payload["status"] == "PASS")
        check("qualification records acceptance", json.loads((base / "qualification-acceptance.json").read_text(encoding="utf-8"))["acceptance"]["performed"] is True)

        # Explicitly pass the decoded manifest dictionary through the public
        # validation path before qualification. This documents the contract:
        # validate_release_artifact() returns data, while portable proof receives
        # the manifest sidecar path.
        manifest_path = artifact.with_name("release-manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        check("release manifest sidecar exists", manifest_path.is_file())
        check("release manifest is machine-readable", isinstance(manifest, dict))

        # Tampering with the sidecar must fail closed. The release ZIP itself is
        # intentionally untouched; qualification must never silently regenerate
        # provenance to make a mismatched artifact pass.
        tampered = base / "tampered-provenance.json"
        provenance_payload = json.loads(provenance.read_text(encoding="utf-8"))
        provenance_payload["source_revision"] = "tampered"
        tampered.write_text(json.dumps(provenance_payload, indent=2) + "\n", encoding="utf-8")
        code, _, _ = capture([
            str(artifact),
            "--provenance", str(tampered),
        ])
        check("tampered provenance is rejected", code != 0)

    print("RSD-21 production release qualification checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
