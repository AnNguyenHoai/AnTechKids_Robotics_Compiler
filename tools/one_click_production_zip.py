#!/usr/bin/env python3
"""B2.7 one-click Windows production ZIP builder.

This is the developer-side bootstrap boundary. It may use a host Python only to
construct the release. The generated RoboStudio release remains artifact-closed:
RoboStudio.exe, portable Python, PlatformIO, ESP32 platform/packages, compiler,
firmware and runtime resources are prepared automatically before B2.6 finalizes
the production ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

PYTHON_RUNTIME_VERSION = "3.10.11"
PYTHON_EMBED_URL = (
    "https://www.python.org/ftp/python/"
    f"{PYTHON_RUNTIME_VERSION}/python-{PYTHON_RUNTIME_VERSION}-embed-amd64.zip"
)
PLATFORMIO_CORE_VERSION = "6.1.18"
BUILD_SCHEMA = "antechkids.robostudio.one-click-production-build"
BUILD_SCHEMA_VERSION = 1
FORBIDDEN_DIRS = {"__pycache__", ".pytest_cache", ".git", ".venv", ".pio", "penv"}
XTENSA_TOOLCHAIN_PACKAGE = "toolchain-xtensa-esp32"


class OneClickBuildError(RuntimeError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print("[run] " + " ".join(f'"{part}"' if " " in part else part for part in command), flush=True)
    result = subprocess.run(command, cwd=cwd, env=env)
    if result.returncode != 0:
        raise OneClickBuildError(f"Command failed with exit code {result.returncode}: {command[0]}")


def _capture(command: list[str], *, cwd: Path | None = None) -> str:
    try:
        return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise OneClickBuildError(f"Unable to run {' '.join(command)}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source_layout(root: Path) -> None:
    required = [
        root / "robostudio" / "main.py",
        root / "robot-platform" / "platformio.ini",
        root / "robot-platform" / "wifi_config.py",
        root / "robot-platform" / "main",
        root / "robot-compiler" / "main.py",
        root / "robot-frontend-robosim" / "frontend" / "__init__.py",
        root / "packages" / "robot-isa" / "target_profiles.json",
        root / "tools" / "one_command_production_build.py",
        root / "tools" / "copy_run_release.py",
        root / "VERSION",
        root / "scripts" / "production-build-requirements.txt",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    if missing:
        raise OneClickBuildError("Repository is missing required production inputs: " + ", ".join(missing))


def _validate_build_host() -> None:
    if os.name != "nt":
        raise OneClickBuildError("B2.7 production ZIP bootstrap must run on Windows")
    if not ((3, 10) <= sys.version_info[:2] < (3, 14)):
        raise OneClickBuildError(
            f"Build Python must be 3.10-3.13; current interpreter is {sys.version.split()[0]}"
        )
    if struct.calcsize("P") * 8 != 64:
        raise OneClickBuildError("Build Python must be 64-bit")


def _git_revision(root: Path, *, allow_dirty: bool) -> str:
    revision = _capture(["git", "rev-parse", "HEAD"], cwd=root)
    dirty = _capture(["git", "status", "--porcelain", "--untracked-files=no"], cwd=root)
    if dirty and not allow_dirty:
        raise OneClickBuildError(
            "Tracked source files are modified. Commit/stash them before a production build, "
            "or pass --allow-dirty explicitly."
        )
    return revision


def _read_version(root: Path) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", version):
        raise OneClickBuildError(f"Invalid VERSION: {version!r}")
    return version


def _venv_python(venv: Path) -> Path:
    return venv / "Scripts" / "python.exe"


def _ensure_build_venv(root: Path, build_root: Path, *, offline: bool) -> Path:
    venv = build_root / "build-venv"
    python = _venv_python(venv)
    if not python.is_file():
        if offline:
            raise OneClickBuildError("Offline build requested but build virtualenv is not prepared")
        _run([sys.executable, "-m", "venv", str(venv)], cwd=root)
    if offline:
        probe = subprocess.run(
            [str(python), "-c", "import PyInstaller, PySide6, yaml"],
            cwd=root,
        )
        if probe.returncode != 0:
            raise OneClickBuildError("Offline build virtualenv is missing PyInstaller/PySide6/PyYAML")
    else:
        _run([
            str(python), "-m", "pip", "install", "--disable-pip-version-check",
            "-r", str(root / "scripts" / "production-build-requirements.txt"),
        ], cwd=root)
    return python


def _build_robostudio(root: Path, build_python: Path, work: Path) -> Path:
    dist = work / "app"
    pyinstaller_work = work / "pyinstaller" / "work"
    spec = work / "pyinstaller" / "spec"
    for path in (dist, pyinstaller_work, spec):
        path.mkdir(parents=True, exist_ok=True)
    command = [
        str(build_python), "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "RoboStudio",
        "--paths", str(root), "--paths", str(root / "robostudio"),
        "--hidden-import", "tools.runtime_preflight",
        "--hidden-import", "PySide6.QtSerialPort",
        "--distpath", str(dist), "--workpath", str(pyinstaller_work), "--specpath", str(spec),
        str(root / "robostudio" / "main.py"),
    ]
    _run(command, cwd=root)
    executable = dist / "RoboStudio.exe"
    if not executable.is_file() or executable.stat().st_size == 0:
        raise OneClickBuildError("PyInstaller did not produce RoboStudio.exe")
    return executable


def _portable_python_valid(root: Path) -> bool:
    return (
        (root / "python.exe").is_file()
        and bool(list(root.glob("python*.dll")))
        and (bool(list(root.glob("python*.zip"))) or (root / "Lib" / "encodings" / "__init__.py").is_file())
    )


def _download(url: str, destination: Path, *, offline: bool) -> None:
    if destination.is_file():
        return
    if offline:
        raise OneClickBuildError(f"Offline build cache is missing: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.unlink(missing_ok=True)
    print(f"[download] {url}", flush=True)
    try:
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(destination)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        raise OneClickBuildError(f"Unable to download {url}: {exc}") from exc


def _discover_cached_python(root: Path, cache: Path) -> Path | None:
    candidates: list[Path] = []
    override = os.environ.get("ROBOSTUDIO_PORTABLE_PYTHON_ROOT", "").strip()
    if override:
        candidates.append(Path(override).expanduser())
    candidates.extend([
        root / "runtime" / "bin",
        root / ".runtime" / "bin",
        root / ".build" / "runtime" / "bin",
        cache / f"python-{PYTHON_RUNTIME_VERSION}" / "bin",
    ])
    for candidate in candidates:
        candidate = candidate.resolve()
        if _portable_python_valid(candidate):
            print(f"[detect] portable Python: {candidate}")
            return candidate
    return None


def _configure_embedded_python(runtime_bin: Path) -> None:
    pth_files = sorted(runtime_bin.glob("python*._pth"))
    if not pth_files:
        raise OneClickBuildError("Embedded Python _pth file is missing")
    stdlib_zips = sorted(runtime_bin.glob("python*.zip"))
    if not stdlib_zips:
        raise OneClickBuildError("Embedded Python standard-library ZIP is missing")
    relative_zip = stdlib_zips[0].name
    pth_files[0].write_text(
        f"{relative_zip}\n.\nLib\nLib\\site-packages\nimport site\n",
        encoding="utf-8",
    )
    (runtime_bin / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)


def _remove_forbidden(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and path.name.lower() in FORBIDDEN_DIRS:
            shutil.rmtree(path, ignore_errors=True)


def _prepare_portable_python(root: Path, build_python: Path, work: Path, cache: Path, *, offline: bool) -> Path:
    destination = work / "prepared" / "runtime" / "bin"
    if destination.exists():
        shutil.rmtree(destination)
    source = _discover_cached_python(root, cache)
    if source is None:
        archive = cache / f"python-{PYTHON_RUNTIME_VERSION}-embed-amd64.zip"
        _download(PYTHON_EMBED_URL, archive, offline=offline)
        extracted = cache / f"python-{PYTHON_RUNTIME_VERSION}" / "bin"
        if not _portable_python_valid(extracted):
            if extracted.parent.exists():
                shutil.rmtree(extracted.parent)
            extracted.mkdir(parents=True)
            try:
                with zipfile.ZipFile(archive) as zf:
                    zf.extractall(extracted)
            except (OSError, zipfile.BadZipFile) as exc:
                raise OneClickBuildError(f"Invalid embedded Python archive: {archive}") from exc
        source = extracted
    shutil.copytree(source, destination)
    _configure_embedded_python(destination)
    site_packages = destination / "Lib" / "site-packages"
    if offline:
        probe = subprocess.run([
            str(destination / "python.exe"), "-I", "-c", "import platformio, yaml, pip"
        ])
        if probe.returncode != 0:
            raise OneClickBuildError(
                "Offline portable Python cache does not contain PlatformIO, PyYAML and pip"
            )
    else:
        # PlatformIO's package manager invokes this same embedded interpreter as
        # `python -m pip` while provisioning tool packages (for example
        # tool-esptoolpy/_contrib). Therefore pip is part of the production
        # runtime closure, not merely a developer-side build dependency.
        _run([
            str(build_python), "-m", "pip", "install", "--disable-pip-version-check",
            "--no-compile", "--upgrade", "--target", str(site_packages),
            f"platformio=={PLATFORMIO_CORE_VERSION}", "PyYAML>=6,<7", "pip>=24,<27",
        ], cwd=root)
    _remove_forbidden(destination)
    _run([
        str(destination / "python.exe"), "-I", "-c",
        "import platformio, yaml, pip; print('portable runtime imports: PASS')",
    ], cwd=root)
    return destination


def _platform_spec(root: Path) -> str:
    text = (root / "robot-platform" / "platformio.ini").read_text(encoding="utf-8")
    match = re.search(r"(?m)^\s*platform\s*=\s*([^;\r\n]+)", text)
    if not match:
        raise OneClickBuildError("platformio.ini does not declare a platform")
    value = match.group(1).strip()
    if "@" not in value or any(ch in value.rsplit("@", 1)[1] for ch in "^~<>=*! ,"):
        raise OneClickBuildError(f"Production PlatformIO platform must be exactly pinned: {value}")
    return value


def _copy_tree_clean(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(*FORBIDDEN_DIRS))
    _remove_forbidden(destination)


def _xtensa_toolchain_root(packages: Path) -> Path:
    return packages / XTENSA_TOOLCHAIN_PACKAGE


def _xtensa_toolchain_structure_error(packages: Path) -> str | None:
    """Return a reason when a cached ESP32 Xtensa toolchain is incomplete."""
    toolchain = _xtensa_toolchain_root(packages)
    if not toolchain.is_dir():
        return f"missing {XTENSA_TOOLCHAIN_PACKAGE} package"

    gxx = toolchain / "bin" / "xtensa-esp32-elf-g++.exe"
    assembler = toolchain / "bin" / "xtensa-esp32-elf-as.exe"
    if not gxx.is_file():
        return "missing xtensa-esp32-elf-g++.exe"
    if not assembler.is_file():
        return "missing xtensa-esp32-elf-as.exe"

    libexec = toolchain / "libexec" / "gcc" / "xtensa-esp32-elf"
    if not libexec.is_dir() or not any(libexec.glob("*/cc1plus.exe")):
        return "missing GCC cc1plus.exe"
    return None


def _probe_xtensa_toolchain(packages: Path, scratch_root: Path) -> tuple[bool, str]:
    """Exercise the cached compiler far enough to spawn cc1plus and assembler."""
    structure_error = _xtensa_toolchain_structure_error(packages)
    if structure_error:
        return False, structure_error

    toolchain = _xtensa_toolchain_root(packages)
    gxx = toolchain / "bin" / "xtensa-esp32-elf-g++.exe"
    probe_root = scratch_root / "xtensa-toolchain-smoke"
    if probe_root.exists():
        shutil.rmtree(probe_root, ignore_errors=True)
    probe_root.mkdir(parents=True, exist_ok=True)
    source = probe_root / "probe.cpp"
    obj = probe_root / "probe.o"
    source.write_text("int probe() { return 0; }\n", encoding="utf-8")
    env = os.environ.copy()
    env["PATH"] = str(toolchain / "bin") + os.pathsep + env.get("PATH", "")
    try:
        result = subprocess.run(
            [str(gxx), "-c", str(source), "-o", str(obj)],
            cwd=probe_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"toolchain smoke test could not run: {exc}"
    finally:
        source.unlink(missing_ok=True)

    if result.returncode != 0 or not obj.is_file():
        detail = (result.stderr or result.stdout or "compiler returned no diagnostic").strip()
        if len(detail) > 500:
            detail = detail[-500:]
        return False, f"toolchain smoke test failed: {detail}"
    shutil.rmtree(probe_root, ignore_errors=True)
    return True, ""


def _purge_xtensa_toolchain(core_cache: Path) -> None:
    """Remove only the broken compiler package plus package-manager temp cache."""
    shutil.rmtree(_xtensa_toolchain_root(core_cache / "packages"), ignore_errors=True)
    shutil.rmtree(core_cache / ".cache", ignore_errors=True)
    shutil.rmtree(core_cache / "packages" / "_tmp", ignore_errors=True)


def _platformio_core_cache(cache: Path, platform_spec: str) -> Path:
    """Return a deliberately short, whitespace-free PlatformIO service root."""
    if any(ch.isspace() for ch in str(cache)):
        raise OneClickBuildError(
            "ROBOSTUDIO_BUILD_CACHE must not contain spaces for the Windows ESP32 toolchain: "
            + str(cache)
        )
    platform_version = platform_spec.rsplit("@", 1)[1]
    return cache / f"pio-{PLATFORMIO_CORE_VERSION}-e32-{platform_version}"


def _prepare_platformio_payload(root: Path, runtime_python: Path, work: Path, cache: Path, *, offline: bool) -> Path:
    platform_spec = _platform_spec(root)
    core_cache = _platformio_core_cache(cache, platform_spec)
    core_cache.mkdir(parents=True, exist_ok=True)
    print(f"[pio] core cache: {core_cache}", flush=True)

    env = os.environ.copy()
    env["PLATFORMIO_CORE_DIR"] = str(core_cache)
    env.pop("PLATFORMIO_HOME_DIR", None)
    env.pop("PLATFORMIO_PLATFORMS_DIR", None)
    env.pop("PLATFORMIO_PACKAGES_DIR", None)

    platforms = core_cache / "platforms"
    packages = core_cache / "packages"
    cache_ready = (
        platforms.is_dir()
        and packages.is_dir()
        and any(platforms.iterdir())
        and any(packages.iterdir())
    )
    if not cache_ready and offline:
        raise OneClickBuildError("Offline PlatformIO/ESP32 cache is not prepared")

    # Keep both the toolchain and the real PlatformIO project on short paths.
    # This matters on Windows because the ESP32 GCC driver spawns cc1plus/as and
    # the full Arduino command line is much larger than a tiny compiler probe.
    probe_root = core_cache / "p"

    if offline:
        healthy, reason = _probe_xtensa_toolchain(packages, core_cache)
        if not healthy:
            raise OneClickBuildError(
                "Offline PlatformIO cache contains an unusable Xtensa toolchain: " + reason
            )
    else:
        _copy_tree_clean(root / "robot-platform", probe_root)
        command = [
            str(runtime_python), "-I", "-m", "platformio", "run",
            "--project-dir", str(probe_root), "-e", "esp32dev", "-j", "1",
        ]
        try:
            _run(command, cwd=probe_root, env=env)
        except OneClickBuildError:
            healthy, reason = _probe_xtensa_toolchain(packages, core_cache)
            if healthy:
                raise
            print("[repair] cached Xtensa toolchain is unusable: " + reason, flush=True)
            print(
                "[repair] removing the broken toolchain package and retrying PlatformIO provisioning once",
                flush=True,
            )
            _purge_xtensa_toolchain(core_cache)
            _copy_tree_clean(root / "robot-platform", probe_root)
            _run(command, cwd=probe_root, env=env)

        healthy, reason = _probe_xtensa_toolchain(packages, core_cache)
        if not healthy:
            raise OneClickBuildError(
                "PlatformIO provisioning completed but the Xtensa toolchain is unusable: " + reason
            )

    if not platforms.is_dir() or not packages.is_dir() or not any(platforms.iterdir()) or not any(packages.iterdir()):
        raise OneClickBuildError("PlatformIO provisioning did not produce platforms/ and packages/")

    destination = work / "prepared" / "runtime" / "platformio"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    _copy_tree_clean(platforms, destination / "platforms")
    _copy_tree_clean(packages, destination / "packages")
    shutil.rmtree(probe_root, ignore_errors=True)
    return destination


def _prepare_resources(root: Path, work: Path) -> Path:
    source = root / "packages" / "robot-isa" / "target_profiles.json"
    destination = work / "prepared" / "runtime" / "resources"
    if destination.exists():
        shutil.rmtree(destination)
    target = destination / "robot-isa" / "target_profiles.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return destination


def _build_release(root: Path, build_python: Path, executable: Path, runtime_bin: Path, runtime_platformio: Path, resources: Path, revision: str, output: Path) -> None:
    _run([
        str(build_python), str(root / "tools" / "one_command_production_build.py"),
        "--executable", str(executable),
        "--runtime-bin", str(runtime_bin),
        "--runtime-platformio", str(runtime_platformio),
        "--runtime-resources", str(resources),
        "--firmware-root", str(root / "robot-platform"),
        "--version-file", str(root / "VERSION"),
        "--source-revision", revision,
        "--output", str(output),
    ], cwd=root)


def _write_report(root: Path, build_root: Path, artifact: Path, revision: str, version: str) -> Path:
    payload = {
        "schema": BUILD_SCHEMA,
        "schema_version": BUILD_SCHEMA_VERSION,
        "status": "PASS",
        "source_revision": revision,
        "application_version": version,
        "artifact": str(artifact.relative_to(root)),
        "artifact_sha256": _sha256(artifact),
        "builder_python": sys.version.split()[0],
        "portable_python": PYTHON_RUNTIME_VERSION,
        "platformio_core": PLATFORMIO_CORE_VERSION,
        "platformio_platform": _platform_spec(root),
        "entrypoint": "RoboStudio.cmd",
    }
    path = build_root / "one-click-build-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _print_plan(root: Path) -> None:
    print("B2.7 one-click production ZIP plan")
    print(f"Repository: {root}")
    print("1. Create/reuse .build/production/build-venv")
    print("2. Build RoboStudio.exe with PyInstaller")
    print(f"3. Detect/cache Python {PYTHON_RUNTIME_VERSION} embeddable runtime")
    print(f"4. Install PlatformIO Core {PLATFORMIO_CORE_VERSION} into artifact Python")
    print(f"5. Provision {_platform_spec(root)} by compiling robot-platform/esp32dev")
    print("6. Stage packages/robot-isa/target_profiles.json")
    print("7. Run B2.6 one-command production builder/finalizer")
    print("8. Emit releases/production/RoboStudio-<VERSION>-Windows.zip")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a complete RoboStudio production ZIP without manual runtime paths")
    parser.add_argument("--offline", action="store_true", help="use only previously prepared build/runtime caches")
    parser.add_argument("--clean", action="store_true", help="remove the disposable B2.7 work directory before building")
    parser.add_argument("--allow-dirty", action="store_true", help="allow tracked source modifications (not recommended for production)")
    parser.add_argument("--keep-work", action="store_true", help="keep disposable staging after a successful build")
    parser.add_argument("--plan", action="store_true", help="validate source layout and print the automatic build plan without changing files")
    parser.add_argument("--output", type=Path, help="production release output directory")
    args = parser.parse_args(argv)

    root = repo_root()
    try:
        _validate_source_layout(root)
        if args.plan:
            _print_plan(root)
            return 0
        _validate_build_host()
        revision = _git_revision(root, allow_dirty=args.allow_dirty)
        version = _read_version(root)
        build_root = root / ".build" / "production"
        work = build_root / "work"
        cache = Path(os.environ.get("ROBOSTUDIO_BUILD_CACHE", str(build_root / "cache"))).expanduser().resolve()
        if args.clean and work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)

        print(f"[source] revision={revision}")
        print(f"[source] version={version}")
        build_python = _ensure_build_venv(root, build_root, offline=args.offline)
        executable = _build_robostudio(root, build_python, work)
        runtime_bin = _prepare_portable_python(root, build_python, work, cache, offline=args.offline)
        runtime_platformio = _prepare_platformio_payload(root, runtime_bin / "python.exe", work, cache, offline=args.offline)
        resources = _prepare_resources(root, work)
        output = (args.output or (root / "releases" / "production")).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        _build_release(root, build_python, executable, runtime_bin, runtime_platformio, resources, revision, output)
        artifact = output / f"RoboStudio-{version}-Windows.zip"
        if not artifact.is_file():
            raise OneClickBuildError(f"Expected production artifact was not created: {artifact}")
        report = _write_report(root, build_root, artifact, revision, version)
        print("\n=== B2.7 ONE-CLICK PRODUCTION BUILD: PASS ===")
        print(f"ZIP: {artifact}")
        print(f"SHA-256: {_sha256(artifact)}")
        print(f"Report: {report}")
        if not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)
        return 0
    except (OneClickBuildError, OSError, ValueError) as exc:
        print(f"B2.7 one-click production build: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
