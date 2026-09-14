"""RSD-21.7 real compiler integration regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_distribution, production_e2e, release_package


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _make_app(path: Path) -> None:
    path.write_text(
        "import sys\n"
        "if '--self-test' in sys.argv:\n"
        "    print('ROBOSTUDIO_E2E_READY')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )


def main() -> int:
    compiler_root = ROOT / "robot-compiler"
    compiler_main = compiler_root / "main.py"
    compiler_package = compiler_root / "compiler"
    check("real compiler source exists", compiler_main.is_file())
    check("real compiler package exists", compiler_package.is_dir())

    with tempfile.TemporaryDirectory(prefix="rsd-21-7-test-") as td:
        base = Path(td)
        inputs = base / "inputs"
        inputs.mkdir()
        executable = inputs / "RoboStudio.exe"
        _make_app(executable)
        (inputs / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        resources = inputs / "resources"
        (resources / "robot-isa").mkdir(parents=True)
        (resources / "robot-isa" / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")
        output = base / "distribution"

        result = production_distribution.build_production_distribution(
            production_distribution.ProductionDistributionInputs(
                executable=executable,
                runtime_resources=resources,
                version_file=inputs / "VERSION",
                compiler_root=compiler_root,
            ),
            output,
        )
        distribution = result.distribution_root
        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        compiler_entry = distribution / "compiler" / "main.py"
        compiler_package = distribution / "compiler" / "compiler"

        check("production distribution is created", distribution.is_dir())
        check("production distribution contains real compiler entry", compiler_entry.is_file())
        check("production distribution contains real compiler package", compiler_package.is_dir())
        check("compiler is recorded in distribution manifest", manifest["compiler"] == "compiler/main.py")
        check("compiler source is free of developer cache", not any(p.name == "__pycache__" for p in (distribution / "compiler").rglob("*")))
        check("Python remains external", not (distribution / "runtime" / "bin").exists())
        check("PlatformIO remains external", not (distribution / "runtime" / "platformio").exists())

        artifact = base / "RoboStudio-1.2.3-Windows.zip"
        release = release_package.build_release(distribution, artifact)
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("production release ZIP is created", artifact.is_file())
        check("ZIP contains compiler entry", "compiler/main.py" in names)
        check("ZIP contains compiler implementation", "compiler/compiler/compiler.py" in names)
        check("ZIP excludes Python runtime", not any(name.startswith("runtime/bin/") for name in names))
        check("ZIP excludes PlatformIO runtime", not any(name.startswith("runtime/platformio/") for name in names))
        check("ZIP validates", release_package.validate_release_artifact(artifact, release.manifest)["production_boundary"] is True)

        source = base / "sample.py"
        source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")
        result = production_e2e.evaluate_production_artifact(
            artifact=artifact,
            source=source,
            launch=True,
            launch_command=[sys.executable, "{app}", "--self-test"],
            compile_command=[sys.executable, "{compiler}", "--file", "{source}", "--output", "{output}"],
        )
        report = result.to_dict()
        check("RoboStudio starts from extracted production ZIP", report["robostudio_started"] is True)
        check("real compiler executes from extracted production ZIP", report["compiler_succeeded"] is True)
        check("compiler evidence points into extracted artifact", report["evidence"]["compiler"] == "compiler/main.py")
        check("compiler output is produced", report["evidence"]["compiler_output"] == "e2e-output/program.h")
        check("E2E status is PASS", report["status"] == "PASS")
        check("E2E evidence is JSON serializable", bool(json.dumps(report)))

    print("RSD-21.7 Real Compiler Integration checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
