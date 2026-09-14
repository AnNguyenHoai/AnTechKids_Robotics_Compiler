"""RSD-17 production distribution builder tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_distribution, production_artifact_boundary, runtime_preflight


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except production_distribution.ProductionDistributionError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_inputs(root: Path) -> production_distribution.ProductionDistributionInputs:
    executable = root / "app-build" / "RoboStudio.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"production-executable")
    (executable.parent / "Qt6Core.dll").write_bytes(b"application-local-dll")

    version = root / "VERSION"
    version.write_text("7.2.0\n", encoding="utf-8")

    compiler = root / "compiler"
    (compiler / "compiler").mkdir(parents=True)
    (compiler / "main.py").write_text("print('compiler')\n", encoding="utf-8")
    (compiler / "compiler" / "__init__.py").write_text("", encoding="utf-8")

    frontend = root / "frontend"
    frontend.mkdir()
    (frontend / "__init__.py").write_text("", encoding="utf-8")
    (frontend / "rewriter.py").write_text("def rewrite(source):\n    return source\n", encoding="utf-8")

    resources = root / "resources"
    profile = resources / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text('{"targets": []}\n', encoding="utf-8")

    from tools import runtime_resources
    runtime_resources.write_resource_manifest(resources)

    return production_distribution.ProductionDistributionInputs(
        executable=executable,
        runtime_resources=resources,
        version_file=version,
        compiler_root=compiler,
        frontend_root=frontend,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd17-") as temp:
        root = Path(temp)
        inputs = make_inputs(root)
        output = root / "distribution"

        old_cwd = Path.cwd()
        os.chdir(root / "app-build")
        try:
            result = production_distribution.build_production_distribution(inputs, output)
        finally:
            os.chdir(old_cwd)

        check("production distribution is created", result.distribution_root.is_dir())
        check("application is copied", (output / "RoboStudio.exe").is_file())
        check("application-local DLL is copied", (output / "Qt6Core.dll").is_file())
        check("repository VERSION is integrated", (output / "VERSION").read_text(encoding="utf-8").strip() == "7.2.0")
        check("bundled Python is not included", not (output / "runtime" / "bin").exists())
        check("bundled PlatformIO is not included", not (output / "runtime" / "platformio").exists())
        check("runtime resources are included", (output / "runtime" / "resources" / "robot-isa" / "target_profiles.json").is_file())
        check("application-owned compiler is included", (output / "compiler" / "main.py").is_file())
        check("RoboSim frontend is included", (output / "compiler" / "frontend" / "rewriter.py").is_file())
        check("distribution passes runtime preflight", runtime_preflight.validate_distribution(output).application_root == output)
        check("production artifact boundary passes", production_artifact_boundary.validate_distribution_root(output)["status"] == "PASS")

        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        check("distribution manifest records application", manifest["application"] == "RoboStudio.exe")
        check("distribution manifest records production portability", manifest["portable"] is False)
        check("distribution manifest records application-local DLL", any(item["path"] == "Qt6Core.dll" for item in manifest["files"]))
        check("distribution VERSION is not source-relative", Path(manifest["files"][0]["path"]).is_absolute() is False)
        check("distribution manifest records compiler", manifest["compiler"] == "compiler/main.py")
        check("distribution manifest records compiler contract", manifest["compiler_contract"] == "compiler/robostudio_bridge.py")

        missing_version = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable,
            runtime_resources=inputs.runtime_resources,
            version_file=root / "missing-VERSION",
            compiler_root=inputs.compiler_root,
            frontend_root=inputs.frontend_root,
        )
        expect_error(
            "missing production VERSION is rejected",
            lambda: production_distribution.build_production_distribution(missing_version, root / "bad-version"),
            "VERSION",
        )

        bad_compiler = root / "bad-compiler"
        bad_compiler.mkdir()
        bad_inputs = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable,
            runtime_resources=inputs.runtime_resources,
            version_file=inputs.version_file,
            compiler_root=bad_compiler,
            frontend_root=inputs.frontend_root,
        )
        expect_error(
            "invalid application-owned compiler is rejected",
            lambda: production_distribution.build_production_distribution(bad_inputs, root / "bad-compiler-output"),
            "application-owned compiler",
        )

        forbidden = output / "runtime" / "bin"
        forbidden.mkdir(parents=True)
        (forbidden / "python.exe").write_bytes(b"forbidden")
        try:
            production_artifact_boundary.validate_distribution_root(output)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
            check("bundled Python payload is rejected by production boundary", "runtime/bin" in str(exc))
        else:
            raise AssertionError("bundled Python payload is not rejected")

    print("RSD-17 production distribution checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
