"""Stage the PlatformIO deployment runtime for a RoboStudio release.

This tool is intentionally a *release-build* tool. It does not install or
modify PlatformIO on the developer machine. It copies an already provisioned
PlatformIO Core directory into the RoboStudio runtime layout and writes a
machine-readable manifest. The final application can then point PlatformIO at
that private core directory through ``PLATFORMIO_CORE_DIR``.

Windows virtual environments are not assumed to be relocatable. Therefore a
release must provide a portable Python runtime separately (RSD-03) and install
PlatformIO into that runtime. The packager rejects a source ``penv`` by default
so a host-specific Python reference cannot accidentally enter the release.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

PLATFORMIO_DIRS = ("platforms", "packages")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_tree(source: Path, destination: Path) -> int:
    if not source.is_dir():
        raise RuntimeError(f"Missing deployment runtime directory: {source}")
    files = 0
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        files += 1
    return files


def package_runtime(source: Path, output: Path, *, allow_penv: bool = False) -> dict:
    source = source.resolve()
    output = output.resolve()
    if source == output or source in output.parents:
        raise RuntimeError("Output runtime directory must not be inside the source PlatformIO Core directory.")
    if not source.is_dir():
        raise RuntimeError(f"PlatformIO Core directory not found: {source}")

    penv = source / "penv"
    if penv.exists() and not allow_penv:
        raise RuntimeError(
            "Refusing to package PlatformIO penv because Windows virtual environments "
            "can retain host-specific interpreter paths. Package a portable Python "
            "runtime separately, then install PlatformIO into it."
        )

    for relative in PLATFORMIO_DIRS:
        if not (source / relative).is_dir():
            raise RuntimeError(f"PlatformIO Core is incomplete: missing {relative}/")

    runtime_root = output
    runtime_root.mkdir(parents=True, exist_ok=True)
    file_count = 0
    for relative in PLATFORMIO_DIRS:
        file_count += copy_tree(source / relative, runtime_root / relative)

    # Copy global libraries only when present. They are harmless for the
    # current project and preserve compatibility with PlatformIO LDF.
    if (source / "lib").is_dir():
        file_count += copy_tree(source / "lib", runtime_root / "lib")

    manifest = {
        "schema": "antechkids.robostudio.deployment-runtime",
        "schema_version": 1,
        "platformio_core": {
            "source_not_embedded": True,
            "required_directories": list(PLATFORMIO_DIRS),
            "file_count": file_count,
        },
        "runtime_layout": {
            "core_dir": "runtime/platformio",
            "python": "runtime/bin/python.exe",
            "platformio_module": "platformio",
        },
        "portable_python_required": True,
        "host_virtualenv_included": False,
    }
    manifest_path = runtime_root / "deployment-runtime.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a RoboStudio-owned PlatformIO deployment runtime")
    parser.add_argument("--source", required=True, type=Path, help="Provisioned PlatformIO Core directory")
    parser.add_argument("--output", required=True, type=Path, help="RoboStudio runtime/platformio directory")
    parser.add_argument("--allow-penv", action="store_true", help="Allow copying host-specific PlatformIO penv (development only)")
    args = parser.parse_args()

    manifest = package_runtime(args.source, args.output, allow_penv=args.allow_penv)
    print(f"Deployment runtime staged: {args.output.resolve()}")
    print(f"PlatformIO files copied: {manifest['platformio_core']['file_count']}")
    print(f"Manifest: {args.output.resolve() / 'deployment-runtime.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
