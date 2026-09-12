"""RSD-20-P production portable-release proof regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, portable_release_proof, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except portable_release_proof.PortableReleaseProofError as exc:
        check(name, expected.lower() in str(exc).lower())
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def _minimal_pe(import_name: str | None = None) -> bytes:
    """Create a tiny valid PE image containing one optional DLL import."""
    pe_offset = 0x80
    optional_size = 0xF0
    section_table = pe_offset + 24 + optional_size
    raw_offset = 0x400
    raw_size = 0x200
    data = bytearray(raw_offset + raw_size)
    data[0:2] = b"MZ"
    data[0x3C:0x40] = pe_offset.to_bytes(4, "little")
    data[pe_offset:pe_offset + 4] = b"PE\0\0"
    data[pe_offset + 4:pe_offset + 6] = (0x8664).to_bytes(2, "little")
    data[pe_offset + 6:pe_offset + 8] = (1).to_bytes(2, "little")
    data[pe_offset + 20:pe_offset + 22] = optional_size.to_bytes(2, "little")
    optional = pe_offset + 24
    data[optional:optional + 2] = (0x20B).to_bytes(2, "little")
    import_directory = optional + 112 + 8
    data[import_directory:import_directory + 4] = (0x1000).to_bytes(4, "little")
    section = section_table
    data[section:section + 8] = b".idata\0\0"
    data[section + 8:section + 12] = raw_size.to_bytes(4, "little")
    data[section + 12:section + 16] = (0x1000).to_bytes(4, "little")
    data[section + 16:section + 20] = raw_size.to_bytes(4, "little")
    data[section + 20:section + 24] = raw_offset.to_bytes(4, "little")
    if import_name:
        descriptor = raw_offset
        data[descriptor + 12:descriptor + 16] = (0x1030).to_bytes(4, "little")
        name_offset = raw_offset + 0x30
        encoded = import_name.encode("ascii") + b"\0"
        data[name_offset:name_offset + len(encoded)] = encoded
    return bytes(data)


def _make_distribution(root: Path, *, imported_dll: str | None = None, include_dependency: bool = True, host_path: bool = False) -> Path:
    root.mkdir(parents=True)
    executable = root / "RoboStudio.exe"
    executable.write_bytes(_minimal_pe(imported_dll))
    (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")

    runtime = root / "runtime"
    runtime_bin = runtime / "bin"
    runtime_bin.mkdir(parents=True)
    (runtime_bin / ("python.exe" if sys.platform == "win32" else "python")).write_bytes(b"portable-python")

    platformio = runtime / "platformio"
    (platformio / "platforms" / "espressif32").mkdir(parents=True)
    (platformio / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (platformio / "deployment-runtime.json").write_text(
        json.dumps({
            "schema": "antechkids.robostudio.deployment-runtime",
            "schema_version": 1,
            "portable_python_required": True,
            "host_virtualenv_included": False,
            "runtime_layout": {
                "core_dir": "runtime/platformio",
                "python": "runtime/bin/python.exe" if sys.platform == "win32" else "runtime/bin/python",
            },
            "platformio_core": {"required_directories": ["platforms", "packages"]},
        }, indent=2) + "\n", encoding="utf-8"
    )

    resources = runtime / "resources" / "robot-isa"
    resources.mkdir(parents=True)
    (resources / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")
    runtime_resources.write_resource_manifest(runtime / "resources")
    if imported_dll and include_dependency:
        (root / imported_dll).write_bytes(_minimal_pe())
    if host_path:
        (root / "runtime" / "resources" / "host-config.json").write_text(
            json.dumps({"developer": r"C:\Users\Developer\AppData\Local\Programs\Python\Python310"}) + "\n",
            encoding="utf-8",
        )

    files = distribution_package._file_entries(root)
    (root / distribution_package.DISTRIBUTION_MANIFEST).write_text(
        json.dumps({
            "schema": distribution_package.SCHEMA,
            "schema_version": distribution_package.SCHEMA_VERSION,
            "application": "RoboStudio.exe",
            "portable": True,
            "runtime_root": "runtime",
            "files": files,
        }, indent=2) + "\n", encoding="utf-8"
    )
    return root


def _build_release(distribution: Path, base: Path, name: str) -> Path:
    artifact = base / "release" / f"{name}.zip"
    from tools import release_package
    release_package.build_release(distribution, artifact)
    return artifact


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd20p-") as temp:
        base = Path(temp)

        valid_distribution = _make_distribution(base / "valid", imported_dll="Qt6Core.dll")
        valid_artifact = _build_release(valid_distribution, base, "valid")
        report = portable_release_proof.prove_portable_release(valid_artifact)
        check("valid portable release passes", report.passed)
        check("packaged dependency is counted", report.packaged_dependency_count >= 1)
        check("system/non-packaged dependency findings are absent", not report.findings)
        check("release file count is recorded", report.file_count > 0)
        check("report is machine-readable", portable_release_proof.report_to_dict(report)["status"] == "PASS")

        missing_distribution = _make_distribution(base / "missing", imported_dll="Qt6Core.dll", include_dependency=False)
        missing_artifact = _build_release(missing_distribution, base, "missing")
        expect_error(
            "missing non-system PE dependency is rejected",
            lambda: portable_release_proof.prove_portable_release(missing_artifact),
            "non-system PE dependency is not packaged",
        )

        host_leak = _make_distribution(base / "host-leak", host_path=True)
        host_artifact = _build_release(host_leak, base, "host-leak")
        expect_error(
            "host-specific absolute path is rejected",
            lambda: portable_release_proof.prove_portable_release(host_artifact),
            "host-specific absolute path",
        )

        symlink_artifact = base / "release" / "symlink.zip"
        with zipfile.ZipFile(symlink_artifact, "w") as archive:
            info = zipfile.ZipInfo("link")
            info.external_attr = 0o120777 << 16
            archive.writestr(info, b"target")
        expect_error(
            "symlink member is rejected",
            lambda: portable_release_proof._validate_zip_members(symlink_artifact),
            "symlink",
        )

    print("RSD-20-P production portable release proof checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
