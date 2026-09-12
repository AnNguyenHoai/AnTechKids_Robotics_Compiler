"""RSD-20 release CLI contract tests."""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import zipfile
from pathlib import Path

# When this file is executed directly (`python tests/rsd_20/run_rsd_20.py`),
# Python places tests/rsd_20 on sys.path rather than the repository root.
# Bootstrap the root before importing the shared RSD-20-P fixtures.
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
        check("build reports PASS", "RSD-20 release: PASS" in stdout)
        check("build creates ZIP", (output / "RoboStudio-1.2.3-Windows.zip").is_file())
        check("build creates provenance", (output / "release-provenance.json").is_file())
        check("build creates portable proof", (output / "portable-release-proof.json").is_file())
        check("build creates assembly report", (output / "release-assembly-report.json").is_file())
        check("build failure text is empty", not stderr)

        with zipfile.ZipFile(output / "RoboStudio-1.2.3-Windows.zip") as archive:
            names = set(archive.namelist())
        check("build packages executable-local PE dependency", "Qt6Core.dll" in names)

    print("RSD-20 release CLI checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
