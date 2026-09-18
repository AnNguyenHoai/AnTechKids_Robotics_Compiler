"""RSD-24 clean-machine production acceptance regression suite.

The test treats the extracted production ZIP as the system under test and
executes the compiler with the bundled Python interpreter, while removing
common developer-host Python signals from the child environment.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_artifact_boundary, production_distribution, production_e2e, release_package


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _minimal_app(path: Path) -> None:
    path.write_text(
        "import sys\n"
        "if '--self-test' in sys.argv:\n"
        " print('ROBOSTUDIO_CLEAN_MACHINE_READY')\n"
        " raise SystemExit(0)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )


def _pe_machine(path: Path) -> int:
    data = path.read_bytes()
    if data[:2] != b"MZ":
        raise AssertionError(f"not a PE executable: {path}")
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if data[pe_offset:pe_offset + 4] != b"PE\\0\\0":
        raise AssertionError(f"invalid PE signature: {path}")
    return int.from_bytes(data[pe_offset + 4:pe_offset + 6], "little")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _runtime_fixture(root: Path) -> tuple[Path, Path]:
    """Build a deterministic, isolated interpreter fixture plus PlatformIO layout."""
    runtime_bin = root / "runtime-bin"
    runtime_bin.mkdir(parents=True)
    source_python = Path(sys.executable).resolve()
    python_home = source_python.parent
    bundled_python = runtime_bin / "python.exe"
    shutil.copy2(source_python, bundled_python)
    for dependency in sorted(python_home.glob("*.dll"), key=lambda item: item.name.lower()):
        if dependency.is_file():
            shutil.copy2(dependency, runtime_bin / dependency.name)
    dlls = python_home / "DLLs"
    if dlls.is_dir():
        shutil.copytree(dlls, runtime_bin / "DLLs", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(
        python_home / "Lib",
        runtime_bin / "Lib",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "site-packages"),
    )
    pth = ".\nLib\nLib/site-packages\nimport site\n"
    (runtime_bin / "python._pth").write_text(pth, encoding="utf-8")
    python_dll = next(
        (
            item for item in sorted(runtime_bin.glob("python*.dll"), key=lambda item: item.name.lower())
            if item.name.lower().startswith("python") and item.name[6:-4].isdigit()
        ),
        None,
    )
    if python_dll is not None:
        (runtime_bin / f"{python_dll.stem}._pth").write_text(pth, encoding="utf-8")
    if os.name != "nt":
        bundled_python.chmod(bundled_python.stat().st_mode | 0o111)
    check("bundled Python bytes are preserved", _sha256(source_python) == _sha256(bundled_python))
    check("bundled Python machine type is x64", _pe_machine(bundled_python) == 0x8664)
    check("Python isolation file is created", (runtime_bin / "python._pth").is_file())

    platformio_site = runtime_bin / "Lib" / "site-packages" / "platformio"
    platformio_site.mkdir(parents=True)
    (platformio_site / "__init__.py").write_text(
        "__version__ = 'clean-machine-fixture'\n", encoding="utf-8"
    )

    runtime_platformio = root / "runtime-platformio"
    (runtime_platformio / "platforms" / "espressif32").mkdir(parents=True)
    (runtime_platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    return runtime_bin, runtime_platformio


def _clean_environment() -> dict[str, str]:
    env = dict(os.environ)
    for key in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "CONDA_DEFAULT_ENV",
        "PIPENV_ACTIVE",
        "POETRY_ACTIVE",
    ):
        env.pop(key, None)
    # Do not allow command discovery to find a developer Python/PlatformIO.
    env["PATH"] = str(Path(env.get("SystemRoot", "C:/Windows")) / "System32") if os.name == "nt" else ""
    return env


def _run_bundled_python(python: Path, args: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(python), *args],
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        capture_output=True,
        shell=False,
        timeout=30,
    )


def main() -> int:
    compiler_root = ROOT / "robot-compiler"
    frontend_root = ROOT / "robot-frontend-robosim" / "frontend"
    check("real compiler source exists", (compiler_root / "main.py").is_file())
    check("real frontend source exists", (frontend_root / "rewriter.py").is_file())

    with tempfile.TemporaryDirectory(prefix="rsd-24-clean-machine-") as td:
        base = Path(td)
        inputs = base / "inputs"
        inputs.mkdir()
        executable = inputs / "RoboStudio.exe"
        _minimal_app(executable)
        (inputs / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        resources = inputs / "resources" / "robot-isa"
        resources.mkdir(parents=True)
        (resources / "target_profiles.json").write_text('{"targets":[]}\n', encoding="utf-8")
        runtime_bin, runtime_platformio = _runtime_fixture(inputs)
        dist = base / "distribution"

        production_inputs = production_distribution.ProductionDistributionInputs(
            executable=executable,
            runtime_resources=inputs / "resources",
            version_file=inputs / "VERSION",
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            compiler_root=compiler_root,
            frontend_root=frontend_root,
        )
        production_distribution.build_production_distribution(production_inputs, dist)
        artifact = base / "release.zip"
        release = release_package.build_release(dist, artifact)

        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("ZIP contains bundled Python", "runtime/bin/python.exe" in names)
        check(
            "ZIP contains runtime deployment manifest",
            "runtime/platformio/deployment-runtime.json" in names,
        )
        check("ZIP contains compiler", "compiler/main.py" in names)
        check(
            "ZIP passes production boundary",
            release_package.validate_release_artifact(artifact, release.manifest)["production_boundary"] is True,
        )

        extracted = base / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(artifact) as archive:
            archive.extractall(extracted)

        boundary = json.loads(
            (extracted / production_artifact_boundary.BOUNDARY_MANIFEST).read_text(encoding="utf-8")
        )
        check("extracted artifact boundary is PASS", boundary["status"] == "PASS")

        bundled_python = extracted / "runtime" / "bin" / "python.exe"
        compiler = extracted / "compiler" / "main.py"
        check("bundled Python executable exists", bundled_python.is_file())
        check("Python isolation file exists", (bundled_python.parent / "python._pth").is_file())
        check("bundled compiler exists", compiler.is_file())

        env = _clean_environment()
        identity = _run_bundled_python(
            bundled_python,
            [
                "-c",
                "import sys; print(sys.executable); print(sys.prefix); "
                "assert sys.executable.replace('\\\\', '/').lower().endswith('/runtime/bin/python.exe')",
            ],
            extracted,
            env,
        )
        check("bundled interpreter executes", identity.returncode == 0)
        check(
            "interpreter path is inside extracted artifact",
            str(bundled_python).lower().replace("\\", "/") in identity.stdout.lower().replace("\\", "/"),
        )

        source = base / "sample.py"
        source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")
        output = extracted / "e2e-output" / "program.h"
        result = _run_bundled_python(
            bundled_python,
            [str(compiler), "--file", str(source), "--output", str(output)],
            extracted / "compiler",
            env,
        )
        check("compiler executes with bundled Python", result.returncode == 0)
        check("compiler output is produced", output.is_file() and output.stat().st_size > 0)

        app_result = production_e2e.evaluate_production_artifact(
            artifact=artifact,
            source=source,
            launch=True,
            launch_command=["{python}", "{app}", "--self-test"],
            compile_command=["{python}", "{compiler}", "--file", "{source}", "--output", "{output}"],
            environment=env,
        )
        check("production E2E resolves bundled Python", app_result.evidence["bundled_python"] == "runtime/bin/python.exe")\n        check("production E2E does not require target-machine prerequisites", app_result.target_machine_prerequisites is False)
        check("production E2E can use bundled Python", app_result.status == "PASS")
        check("production E2E compiler succeeds", app_result.compiler_succeeded is True)

    print("RSD-24 Clean Machine Production Acceptance checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
