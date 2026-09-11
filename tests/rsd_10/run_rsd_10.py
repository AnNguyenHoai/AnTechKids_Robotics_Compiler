"""RSD-10 portable runtime integrity and version-lock tests."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import runtime_integrity


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except runtime_integrity.RuntimeIntegrityError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_runtime(root: Path) -> None:
    (root / "VERSION").write_text("0.1.1\n", encoding="utf-8")
    (root / "runtime" / "bin").mkdir(parents=True)
    (root / "runtime" / "bin" / "python.exe").write_bytes(b"portable-python-v1")
    core = root / "runtime" / "platformio"
    (core / "platforms" / "espressif32").mkdir(parents=True)
    (core / "platforms" / "espressif32" / "platform.json").write_text(
        '{"name":"espressif32","version":"7.0.1"}\n', encoding="utf-8"
    )
    (core / "packages" / "tool-esptoolpy").mkdir(parents=True)
    (core / "packages" / "tool-esptoolpy" / "version.txt").write_text("4.11.0\n", encoding="utf-8")
    (root / "runtime" / "resources" / "robot-isa").mkdir(parents=True)
    (root / "runtime" / "resources" / "robot-isa" / "target_profiles.json").write_text(
        '{"schema_version":1,"kind":"robot_target_capability_profiles","profiles":[]}\n',
        encoding="utf-8",
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        root.mkdir()
        make_runtime(root)

        manifest_path = runtime_integrity.write_runtime_manifest(root)
        check("runtime integrity manifest is created", manifest_path.is_file())
        manifest = runtime_integrity.validate_runtime_manifest(manifest_path)
        check("complete runtime validates", manifest["portable"] is True)
        check("application version is locked", manifest["application_version"] == "0.1.1")
        check("all required components are recorded", set(runtime_integrity.COMPONENTS) <= set((name, root / rel, kind) for name, rel, kind in runtime_integrity.COMPONENTS))
        check("portable Python is fingerprinted", "portable_python" in manifest["components"])
        check("PlatformIO core is fingerprinted", "platformio_core" in manifest["components"])
        check("PlatformIO packages are fingerprinted", "platformio_packages" in manifest["components"])
        check("resources are fingerprinted", "runtime_resources" in manifest["components"])

        (root / "runtime" / "bin" / "python.exe").write_bytes(b"tampered-python")
        expect_error(
            "runtime binary drift is rejected",
            lambda: runtime_integrity.validate_runtime_manifest(manifest_path),
            "checksum mismatch",
        )

        make_runtime(root)
        runtime_integrity.write_runtime_manifest(root)
        (root / "VERSION").write_text("0.1.2\n", encoding="utf-8")
        expect_error(
            "application version drift is rejected",
            lambda: runtime_integrity.validate_runtime_manifest(manifest_path),
            "application version changed",
        )

        make_runtime(root)
        runtime_integrity.write_runtime_manifest(root)
        (root / "runtime" / "platformio" / "platforms" / "espressif32" / "platform.json").write_text(
            '{"name":"espressif32","version":"9.9.9"}\n', encoding="utf-8"
        )
        expect_error(
            "PlatformIO version/content drift is rejected",
            lambda: runtime_integrity.validate_runtime_manifest(manifest_path),
            "checksum mismatch",
        )

        make_runtime(root)
        runtime_integrity.write_runtime_manifest(root)
        (root / "runtime" / "platformio" / "packages" / "host-only.txt").write_text(
            "host\n", encoding="utf-8"
        )
        expect_error(
            "unexpected runtime files are rejected",
            lambda: runtime_integrity.validate_runtime_manifest(manifest_path),
            "file list changed",
        )

        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw["components"]["portable_python"]["path"] = "../outside"
        manifest_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        expect_error(
            "unsafe component path is rejected",
            lambda: runtime_integrity.validate_runtime_manifest(manifest_path),
            "unsafe path",
        )

    print("RSD-10 runtime integrity checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
