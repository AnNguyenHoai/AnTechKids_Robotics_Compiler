"""P0 — production runtime dependency closure regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, production_runtime_closure, runtime_resources


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_failure(name: str, fn, expected: str) -> None:
    try:
        fn()
    except Exception as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: operation unexpectedly succeeded")


def _make_inputs(root: Path) -> tuple[Path, Path, Path, Path]:
    exe = root / "RoboStudio.exe"
    exe.write_bytes(b"fixture-executable")
    (root / "RoboStudio.dll").write_bytes(b"fixture-local-dependency")

    compiler = root / "compiler-source"
    (compiler / "compiler").mkdir(parents=True)
    (compiler / "frontend").mkdir(parents=True)
    (compiler / "main.py").write_text("print('compiler fixture')\n", encoding="utf-8")
    (compiler / "compiler" / "__init__.py").write_text("\n", encoding="utf-8")
    (compiler / "robostudio_bridge.py").write_text("print('bridge fixture')\n", encoding="utf-8")
    (compiler / "frontend" / "__init__.py").write_text("\n", encoding="utf-8")
    (compiler / "frontend" / "rewriter.py").write_text("def rewrite(source, output): pass\n", encoding="utf-8")

    resources = root / "resources"
    (resources / "robot-isa").mkdir(parents=True)
    (resources / "robot-isa" / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")

    version = root / "VERSION"
    version.write_text("1.0.0\n", encoding="utf-8")
    return exe, compiler, resources, version


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-p0-") as td:
        root = Path(td)
        exe, compiler, resources, version = _make_inputs(root)
        distribution = root / "distribution"
        manifest_path = distribution_package.assemble_distribution(
            distribution_package.DistributionInputs(
                executable=exe,
                runtime_resources=resources,
                production_boundary=True,
                compiler_root=compiler,
                frontend_root=None,
            ),
            distribution,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        check("production manifest is present", manifest_path.is_file())
        check("application executable is packaged", (distribution / "RoboStudio.exe").is_file())
        check("local PE dependency is packaged", (distribution / "RoboStudio.dll").is_file())
        check("compiler entry is packaged", (distribution / "compiler" / "main.py").is_file())
        check("compiler contract is packaged", (distribution / "compiler" / "robostudio_bridge.py").is_file())
        check("frontend entry is packaged", (distribution / "compiler" / "frontend" / "rewriter.py").is_file())
        check("runtime resource manifest is packaged", (distribution / "runtime" / "resources" / runtime_resources.RESOURCE_MANIFEST_NAME).is_file())

        evidence = production_runtime_closure.validate_distribution(distribution)
        check("production dependency closure passes", evidence["status"] == "PASS")
        check("closure records application", evidence["application"] == "RoboStudio.exe")
        check("closure records payload inventory", evidence["payload_file_count"] == len(manifest["files"]))

        evidence_path = production_runtime_closure.write_evidence(distribution, root / "closure.json")
        check("closure evidence is machine-readable", json.loads(evidence_path.read_text(encoding="utf-8"))["status"] == "PASS")

        (distribution / "untracked-runtime.dll").write_bytes(b"not-in-manifest")
        expect_failure(
            "untracked payload is rejected",
            lambda: production_runtime_closure.validate_distribution(distribution),
            "not covered by distribution manifest",
        )
        (distribution / "untracked-runtime.dll").unlink()

        (distribution / "developer-state").mkdir()
        expect_failure(
            "developer-only directory is rejected",
            lambda: production_runtime_closure.validate_distribution(distribution),
            "developer-only payload",
        )
        import shutil
        shutil.rmtree(distribution / "developer-state")

        (distribution / "compiler" / "frontend" / "rewriter.py").unlink()
        expect_failure(
            "missing runtime dependency is rejected",
            lambda: production_runtime_closure.validate_distribution(distribution),
            "checksum mismatch",
        )

    print("P0 production runtime dependency closure checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
