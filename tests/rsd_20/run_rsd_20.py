"""RSD-20 release CLI contract tests."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.rsd_20_p.run_rsd_20_p import _build_release, _make_distribution
from tools import release_cli


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def capture_main(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = release_cli.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd20-") as temp:
        base = Path(temp)
        # The verify/build fixture is intentionally static: it proves release
        # packaging and PE closure without depending on whichever Python happens
        # to be installed on the developer machine. RSD-16 acceptance below gets
        # a separate real interpreter fixture because it actually executes it.
        distribution = _make_distribution(base / "distribution", imported_dll="Qt6Core.dll")
        artifact = _build_release(distribution, base, "RoboStudio-1.2.3-Windows")

        code, stdout, _ = capture_main(["verify", str(artifact)])
        check("verify command succeeds", code == 0)
        check("verify reports PASS", "RSD-20 verify: PASS" in stdout)
        check("verify reports checksum", "SHA-256:" in stdout)

        code, stdout, _ = capture_main(["verify", str(artifact), "--json"])
        check("verify JSON succeeds", code == 0)
        check('verify JSON reports PASS status', '"status": "PASS"' in stdout)

        code, stdout, _ = capture_main(["inspect", str(artifact)])
        check("inspect command succeeds", code == 0)
        check("inspect reports portable", "Portable: True" in stdout)

        output = base / "assembled"
        code, stdout, stderr = capture_main([
            "build",
            "--executable", str(distribution / "RoboStudio.exe"),
            "--runtime-bin", str(distribution / "runtime" / "bin"),
            "--runtime-platformio", str(distribution / "runtime" / "platformio"),
            "--runtime-resources", str(distribution / "runtime" / "resources"),
            "--version-file", str(distribution / "VERSION"),
            "--source-revision", "test-revision",
            "--output", str(output),
        ])
        if code != 0:
            raise AssertionError(f"build command failed:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}")
        # release_cli build delegates to the canonical production release
        # assembly, whose user-facing success prefix is RSD-21.8.
        check("build reports PASS", "RSD-21.8 release: PASS" in stdout)
        check("build creates ZIP", (output / "RoboStudio-1.2.3-Windows.zip").is_file())
        check("build creates provenance", (output / "release-provenance.json").is_file())
        check("build creates portable proof", (output / "portable-release-proof.json").is_file())
        check("build creates assembly report", (output / "release-assembly-report.json").is_file())
        check("build failure text is empty", not stderr)

        with zipfile.ZipFile(output / "RoboStudio-1.2.3-Windows.zip") as archive:
            names = set(archive.namelist())
        check("build packages executable-local PE dependency", "Qt6Core.dll" in names)
        check("build packages real compiler", "compiler/main.py" in names)

        # Clean-machine acceptance is an execution test, so use a real Python
        # runtime only for this artifact. It remains independent of the host's
        # PATH/environment because release_acceptance launches the packaged
        # interpreter by absolute path.
        acceptance_distribution = _make_distribution(
            base / "acceptance-distribution",
            imported_dll="Qt6Core.dll",
            runnable_python=True,
        )
        acceptance_artifact = _build_release(
            acceptance_distribution, base, "RoboStudio-1.2.3-Windows-acceptance"
        )

        evidence = base / "release-acceptance.json"
        code, stdout, stderr = capture_main([
            "accept", str(acceptance_artifact), "--report", str(evidence)
        ])
        check("accept command succeeds", code == 0)
        check("accept reports PASS", "RSD-20 accept: PASS" in stdout)
        check("accept verifies executable", "Executable verified: True" in stdout)
        check("accept verifies environment", "Environment verified: True" in stdout)
        check("accept writes evidence", evidence.is_file())
        check("accept failure text is empty", not stderr)
        evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
        check("evidence has stable schema", evidence_payload["schema"] == "antechkids.robostudio.release-acceptance-evidence")
        check("evidence records artifact checksum", evidence_payload["artifact_sha256"])
        check("evidence records relocation gate", evidence_payload["checks"]["relocation_verified"] is True)
        check("evidence records external CWD gate", evidence_payload["checks"]["external_cwd_verified"] is True)
        check("evidence records environment gate", evidence_payload["checks"]["environment_verified"] is True)
        check("evidence omits temporary extraction path", "relocated_root" not in evidence_payload)

        code, stdout, stderr = capture_main(["accept", str(acceptance_artifact), "--json"])
        check("accept JSON succeeds", code == 0)
        payload = json.loads(stdout)
        check("accept JSON is machine-readable", payload["schema"] == "antechkids.robostudio.clean-machine-release-acceptance")
        check("accept JSON verifies relocation", payload["relocation_verified"] is True)
        check("accept JSON verifies external CWD", payload["external_cwd_verified"] is True)
        check("accept JSON verifies environment", payload["environment_verified"] is True)
        check("accept JSON failure text is empty", not stderr)

    print("RSD-20 release CLI checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
