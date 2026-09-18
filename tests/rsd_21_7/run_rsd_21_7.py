"""RSD-21.7 real compiler integration regression suite."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import shutil
import subprocess
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
        " print('ROBOSTUDIO_E2E_READY')\n"
        " raise SystemExit(0)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )


def _clean_python_environment() -> dict[str, str]:
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
    env["PATH"] = str(Path(env.get("SystemRoot", "C:/Windows")) / "System32") if os.name == "nt" else ""
    return env


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _make_runtime(root: Path) -> tuple[Path, Path]:
    """Create a deterministic, isolated application-owned Python closure."""
    runtime_bin = root / "runtime-bin"
    runtime_bin.mkdir(parents=True)
    python_home = Path(sys.executable).resolve().parent
    source_python = Path(sys.executable).resolve()
    bundled_python = runtime_bin / "python.exe"
    shutil.copy2(source_python, bundled_python)

    # Copy native DLLs from the exact CPython installation selected by CI.
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

    # Isolate the bundled interpreter from registry/environment/user Python.
    pth = ".\nLib\nLib/site-packages\nimport site\n"
    (runtime_bin / "python._pth").write_text(pth, encoding="utf-8")
    python_dll = next(
        (
            item
            for item in sorted(runtime_bin.glob("python*.dll"), key=lambda item: item.name.lower())
            if item.name.lower().startswith("python") and item.name[6:-4].isdigit()
        ),
        None,
    )
    if python_dll is not None:
        (runtime_bin / f"{python_dll.stem}._pth").write_text(pth, encoding="utf-8")

    check("bundled Python bytes are preserved", _sha256(source_python) == _sha256(bundled_python))
    check("bundled Python is a Windows executable", bundled_python.suffix.lower() == ".exe")
    platformio_site = runtime_bin / "Lib" / "site-packages" / "platformio"


def _make_firmware(root: Path) -> Path:
    firmware = root / "firmware"
    (firmware / "main").mkdir(parents=True)
    (firmware / "platformio.ini").write_text(
        "[platformio]\n"
        "src_dir = main\n\n"
        "[env:esp32dev]\n"
        "platform = espressif32@6.12.0\n"
        "board = esp32dev\n"
        "framework = arduino\n\n"
        "[env:esp32dev_ota]\n"
        "extends = env:esp32dev\n"
        "upload_protocol = espota\n\n"
        "[env:esp32dev_bootstrap]\n"
        "extends = env:esp32dev\n",
        encoding="utf-8",
    )
    (firmware / "wifi_config.py").write_text("# clean production fixture\n", encoding="utf-8")
    (firmware / "main" / "main.cpp").write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8")
    return firmware


def main() -> int:
    compiler_root = ROOT / "robot-compiler"
    frontend_root = ROOT / "robot-frontend-robosim" / "frontend"
    check("real compiler source exists", (compiler_root / "main.py").is_file())
    check("real RoboSim frontend exists", (frontend_root / "rewriter.py").is_file())

    with tempfile.TemporaryDirectory(prefix="rsd-21-7-test-") as td:
        base = Path(td)
        inputs = base / "inputs"
        inputs.mkdir()
        exe = inputs / "RoboStudio.exe"
        _make_app(exe)
        (inputs / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        resources = inputs / "resources"
        (resources / "robot-isa").mkdir(parents=True)
        (resources / "robot-isa" / "target_profiles.json").write_text('{"targets":[]}\n', encoding="utf-8")
        runtime_bin, runtime_platformio = _make_runtime(inputs)
        fixture_python = runtime_bin / "python.exe"
        fixture_probe = subprocess.run(
            [str(fixture_python), "-c", "import sys; print(sys.executable); print(sys.prefix); import platformio"],
            cwd=inputs,
            env=_clean_python_environment(),
            check=True,
            text=True,
            capture_output=True,
            shell=False,
            timeout=30,
        )
        check("relocated fixture Python executes before packaging", fixture_python.as_posix().lower() in fixture_probe.stdout.lower())
        firmware = _make_firmware(inputs)
        dist = base / "distribution"

        production_inputs = production_distribution.ProductionDistributionInputs(
            executable=exe,
            runtime_resources=resources,
            version_file=inputs / "VERSION",
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            compiler_root=compiler_root,
            frontend_root=frontend_root,
            firmware_root=firmware,
        )
        result = production_distribution.build_production_distribution(production_inputs, dist)
        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        check("production distribution is created", dist.is_dir())
        check("production distribution contains real compiler entry", (dist / "compiler" / "main.py").is_file())
        check("production distribution contains frontend", (dist / "compiler" / "frontend" / "rewriter.py").is_file())
        check("production distribution contains firmware", (dist / "firmware" / "robot-platform" / "platformio.ini").is_file())
        check("compiler is recorded", manifest["compiler"] == "compiler/main.py")
        check("contract is recorded", manifest["compiler_contract"] == "compiler/robostudio_bridge.py")
        check("bundled Python is packaged", (dist / "runtime" / "bin" / "python.exe").is_file())
        check("Python isolation file is packaged", (dist / "runtime" / "bin" / "python._pth").is_file())
        check("bundled PlatformIO is packaged", (dist / "runtime" / "platformio" / "platforms").is_dir() and (dist / "runtime" / "platformio" / "packages").is_dir())
        check("runtime deployment manifest is packaged", (dist / "runtime" / "platformio" / "deployment-runtime.json").is_file())

        artifact = base / "release.zip"
        release = release_package.build_release(dist, artifact)
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("ZIP contains compiler", "compiler/main.py" in names)
        check("ZIP contains contract", "compiler/robostudio_bridge.py" in names)
        check("ZIP contains frontend", "compiler/frontend/rewriter.py" in names)
        check("ZIP contains bundled Python", "runtime/bin/python.exe" in names)
        check("ZIP contains firmware", "firmware/robot-platform/platformio.ini" in names)
        check("ZIP contains bundled PlatformIO", "runtime/platformio/deployment-runtime.json" in names and ("runtime/platformio/platforms/" in names or any(name.startswith("runtime/platformio/platforms/") for name in names)))
        check("ZIP validates", release_package.validate_release_artifact(artifact, release.manifest)["production_boundary"] is True)

        source = base / "sample.py"
        source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")
        result = production_e2e.evaluate_production_artifact(
            artifact=artifact,
            source=source,
            launch=True,
            launch_command=["{python}", "{app}", "--self-test"],
            compile_command=["{python}", "{compiler}", "--file", "{source}", "--output", "{output}"],
        )
        report = result.to_dict()
        compiler_output = Path(report["evidence"]["compiler_output"]).as_posix() if report["evidence"]["compiler_output"] else None
        check("RoboStudio starts from extracted ZIP", report["robostudio_started"] is True)
        check("real compiler executes", report["compiler_succeeded"] is True)
        check("compiler output produced", compiler_output == "e2e-output/program.h")
        check("E2E PASS", report["status"] == "PASS")

        # Regression guard: corrupting the packaged Python must make the E2E fail.
        broken_artifact = base / "release-broken-python.zip"
        with zipfile.ZipFile(artifact, "r") as source_zip, zipfile.ZipFile(broken_artifact, "w", compression=zipfile.ZIP_DEFLATED) as target_zip:
            for item in source_zip.infolist():
                payload = source_zip.read(item)
                if item.filename == "runtime/bin/python.exe":
                    payload = b"not-a-python-executable"
                target_zip.writestr(item, payload)
        try:
            production_e2e.evaluate_production_artifact(
                artifact=broken_artifact,
                source=source,
                launch=True,
                launch_command=["{python}", "{app}", "--self-test"],
                compile_command=["{python}", "{compiler}", "--file", "{source}", "--output", "{output}"],
            )
        except production_e2e.ProductionE2EError:
            print("PASS: broken bundled Python is rejected")
        else:
            raise AssertionError("broken bundled Python must make production E2E fail")

    print("RSD-21.7 Real Compiler Integration checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
