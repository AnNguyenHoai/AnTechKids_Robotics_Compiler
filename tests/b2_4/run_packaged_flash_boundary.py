#!/usr/bin/env python3
"""B2.4 production artifact + RoboStudio flash-boundary regression gate."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, production_distribution


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _load_rsd17_fixture_module():
    path = ROOT / "tests" / "rsd_17" / "run_rsd_17.py"
    spec = importlib.util.spec_from_file_location("b24_rsd17_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load production fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_production_distribution_contains_flash_runtime(base: Path) -> None:
    fixture = _load_rsd17_fixture_module()
    inputs = fixture.make_inputs(base)
    output = base / "distribution"
    result = production_distribution.build_production_distribution(inputs, output)

    required = tuple(production_distribution.DEPLOYMENT_RUNTIME_TOOL_FILES)
    check("deployment runtime allow-list is non-empty", bool(required))
    for name in required:
        check(f"production artifact contains tools/{name}", (output / "tools" / name).is_file())

    check("production artifact contains USB deploy entry point", (output / "tools" / "deploy_robot.py").is_file())
    check("production artifact contains hardware preflight", (output / "tools" / "hardware_preflight.py").is_file())
    check("production artifact contains target qualification", (output / "tools" / "target_machine_qualification.py").is_file())

    manifest = distribution_package.validate_distribution_manifest(result.manifest)
    paths = {entry["path"] for entry in manifest["files"]}
    check("manifest records deployment tool root", manifest.get("deployment_tools") == "tools")
    check("manifest records USB deploy entry point", "tools/deploy_robot.py" in paths)
    check("manifest records hardware preflight", "tools/hardware_preflight.py" in paths)
    check("manifest records target qualification", "tools/target_machine_qualification.py" in paths)
    check("production distribution schema advanced for flash runtime", production_distribution.PRODUCTION_SCHEMA_VERSION == 5)

    # Development compiler wrappers must not be accidentally introduced merely
    # to make deployment work. deploy_robot now uses compiler/robostudio_bridge.py.
    check("production runtime excludes source rewrite wrapper", not (output / "tools" / "rewrite.py").exists())
    check("production runtime excludes source compile wrapper", not (output / "tools" / "compile.py").exists())


def test_robostudio_flash_surface_contract() -> None:
    service = (ROOT / "robostudio" / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    ui = (ROOT / "robostudio" / "ui" / "robot_tab.py").read_text(encoding="utf-8")
    deploy = (ROOT / "tools" / "deploy_robot.py").read_text(encoding="utf-8")

    check("deployment service resolves canonical application root", "runtime_paths.application_root()" in service)
    check("deployment service validates packaged runtime tool files", "def _runtime_tool" in service)
    check("deployment subprocess CWD uses external user state", ' / "deployment"' in service and "prepare_user_data_root" in service)
    check("first-flash service rejects missing selected port", "Select a detected USB/COM port before first-flash" in service)

    check("First-Flash UI uses a serial port combo", "self.usb_port_combo = QComboBox()" in ui)
    check("First-Flash UI reuses Qt serial inventory", "SerialConsoleService.available_ports()" in ui)
    check("First-Flash UI has explicit USB refresh", "Refresh USB" in ui)
    check("First-Flash UI no longer exposes free-text USB port", "self.usb_port_edit" not in ui)

    check("deployment compiler uses packaged compiler bridge", '"compiler"/"robostudio_bridge.py"' in deploy or '"compiler" / "robostudio_bridge.py"' in deploy)
    check("deployment no longer invokes rewrite wrapper", 'ROOT/"tools"/"rewrite.py"' not in deploy)
    check("deployment no longer invokes compile wrapper", 'ROOT/"tools"/"compile.py"' not in deploy)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-b24-package-") as temp:
        test_production_distribution_contains_flash_runtime(Path(temp))
    test_robostudio_flash_surface_contract()
    print("B2.4 packaged flash runtime boundary checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
