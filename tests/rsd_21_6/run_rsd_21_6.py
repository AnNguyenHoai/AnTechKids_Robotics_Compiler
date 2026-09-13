"""RSD-21.6 production launcher / entry-point regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_distribution, release_package


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-6-test-") as td:
        root = Path(td)
        inputs = root / "inputs"
        executable = inputs / "RoboStudio.exe"
        resources = inputs / "resources"
        output = root / "release"
        inputs.mkdir()
        resources.mkdir()
        executable.write_bytes(b"RSD-21.6-ROBOSTUDIO-FIXTURE")
        (inputs / "Application.dll").write_bytes(b"application-local-dll")
        (inputs / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (resources / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")

        result = production_distribution.build_production_distribution(
            production_distribution.ProductionDistributionInputs(
                executable=executable,
                runtime_resources=resources,
                version_file=inputs / "VERSION",
            ),
            output,
        )
        distribution = result.distribution_root
        launcher = distribution / production_distribution.LAUNCHER_NAME
        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))

        check("production distribution is created", distribution.is_dir())
        check("RoboStudio executable is present", (distribution / "RoboStudio.exe").is_file())
        check("production launcher is present", launcher.is_file())
        check("launcher is Windows command script", launcher.suffix.lower() == ".cmd")
        text = launcher.read_text(encoding="utf-8")
        check("launcher resolves executable from its own directory", "%~dp0RoboStudio.exe" in text)
        check("launcher preserves command arguments", "%*" in text)
        check("launcher does not depend on PATH", "PATH" not in text.upper())
        check("launcher changes cwd to its own directory", 'pushd "%~dp0"' in text)
        check("launcher propagates application exit code", "exit /b %exit_code%" in text)
        check("distribution manifest is machine-readable", bool(manifest["files"]))
        check("launcher is recorded in distribution manifest", any(item["path"] == "RoboStudio.cmd" for item in manifest["files"]))
        check("target prerequisites are not bundled", not (distribution / "runtime" / "bin").exists())
        check("PlatformIO is not bundled", not (distribution / "runtime" / "platformio").exists())

        artifact = root / "RoboStudio-1.0.0-Windows.zip"
        release = release_package.build_release(distribution, artifact)
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
            packaged_launcher = archive.read("RoboStudio.cmd").decode("utf-8")
        check("release ZIP contains launcher", "RoboStudio.cmd" in names)
        check("release ZIP launcher is relocation-safe", "%~dp0RoboStudio.exe" in packaged_launcher)
        check("release ZIP validates", release_package.validate_release_artifact(artifact, release.manifest)["production_boundary"] is True)

    print("RSD-21.6 production launcher checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
