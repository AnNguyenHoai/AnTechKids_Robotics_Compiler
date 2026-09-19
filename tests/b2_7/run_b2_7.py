#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "one_click_production_zip.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("one_click_production_zip", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load B2.7 orchestrator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    module = _load_module()

    # Source topology and the no-side-effect plan must remain runnable on CI.
    module._validate_source_layout(ROOT)
    require(module._platform_spec(ROOT) == "espressif32@6.12.0", "B2.7 must consume the exact production ESP32 platform pin")
    result = subprocess.run([sys.executable, str(MODULE_PATH), "--plan"], cwd=ROOT, capture_output=True, text=True)
    require(result.returncode == 0, f"B2.7 --plan failed: {result.stdout}\n{result.stderr}")
    require("Build RoboStudio.exe with PyInstaller" in result.stdout, "plan must include RoboStudio.exe build")
    require("Run B2.6 one-command production builder/finalizer" in result.stdout, "plan must terminate through B2.6")

    # Portable-runtime discovery must require a real interpreter + DLL + stdlib.
    with tempfile.TemporaryDirectory(prefix="b2-7-runtime-") as td:
        runtime = Path(td)
        (runtime / "python.exe").write_bytes(b"exe")
        require(not module._portable_python_valid(runtime), "python.exe alone must not qualify as a portable runtime")
        (runtime / "python310.dll").write_bytes(b"dll")
        (runtime / "python310.zip").write_bytes(b"stdlib")
        require(module._portable_python_valid(runtime), "portable Python topology should be accepted")

    # PlatformIO service state used during production provisioning must stay on
    # a short whitespace-free path so the legacy ESP32 GCC driver can reliably
    # spawn cc1plus/as on Windows.
    with tempfile.TemporaryDirectory(prefix="b27-cache-") as td:
        cache = Path(td) / "RSC"
        core = module._platformio_core_cache(cache, "espressif32@6.12.0")
        require(core.name == "pio-6.1.18-e32-6.12.0", "PlatformIO core cache name must stay deliberately short")
        require(core.parent == cache, "PlatformIO core cache must live directly below the selected short cache")
        spaced = Path(td) / "cache with spaces"
        try:
            module._platformio_core_cache(spaced, "espressif32@6.12.0")
        except module.OneClickBuildError:
            pass
        else:
            raise AssertionError("PlatformIO production cache must reject whitespace paths")

    # Merging PlatformIO's pinned Python tool payload must preserve both package
    # directories and ordinary files; the full Windows build additionally probes
    # the real esptool wrapper with the embedded interpreter.
    with tempfile.TemporaryDirectory(prefix="b27-python-tool-") as td:
        base = Path(td)
        source_payload = base / "source"
        destination_payload = base / "site-packages"
        (source_payload / "pkg").mkdir(parents=True)
        (source_payload / "pkg" / "module.py").write_text("VALUE=1\n", encoding="utf-8")
        (source_payload / "marker.txt").write_text("ok\n", encoding="utf-8")
        module._merge_tree(source_payload, destination_payload)
        require((destination_payload / "pkg" / "module.py").is_file(), "Python payload merge must preserve package directories")
        require((destination_payload / "marker.txt").is_file(), "Python payload merge must preserve ordinary files")

    # A partially extracted cached Xtensa package must never be accepted just
    # because packages/ is non-empty. This reproduces the Windows failure where
    # g++.exe exists but cannot CreateProcess its cc1plus child.
    with tempfile.TemporaryDirectory(prefix="b2-7-toolchain-") as td:
        core_cache = Path(td) / "platformio-cache"
        packages = core_cache / "packages"
        toolchain = packages / module.XTENSA_TOOLCHAIN_PACKAGE
        bin_dir = toolchain / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "xtensa-esp32-elf-g++.exe").write_bytes(b"g++")
        (bin_dir / "xtensa-esp32-elf-as.exe").write_bytes(b"as")
        reason = module._xtensa_toolchain_structure_error(packages)
        require(reason is not None and "cc1plus" in reason, "B2.7 must reject a cached toolchain missing cc1plus")

        # Repair must be targeted: remove the broken compiler package/temp cache,
        # but preserve unrelated already-provisioned PlatformIO packages.
        framework = packages / "framework-arduinoespressif32"
        framework.mkdir(parents=True)
        (core_cache / ".cache" / "tmp").mkdir(parents=True)
        module._purge_xtensa_toolchain(core_cache)
        require(not toolchain.exists(), "B2.7 repair must remove the broken Xtensa package")
        require(framework.is_dir(), "B2.7 repair must preserve unrelated PlatformIO packages")
        require(not (core_cache / ".cache").exists(), "B2.7 repair must clear stale package-manager cache")

        # A complete static toolchain topology should pass the structural gate.
        bin_dir.mkdir(parents=True)
        (bin_dir / "xtensa-esp32-elf-g++.exe").write_bytes(b"g++")
        (bin_dir / "xtensa-esp32-elf-as.exe").write_bytes(b"as")
        cc1plus = toolchain / "libexec" / "gcc" / "xtensa-esp32-elf" / "8.4.0" / "cc1plus.exe"
        cc1plus.parent.mkdir(parents=True)
        cc1plus.write_bytes(b"cc1plus")
        require(module._xtensa_toolchain_structure_error(packages) is None, "complete Xtensa toolchain topology should be accepted")

    cmd = (ROOT / "BUILD_PRODUCTION_ZIP.cmd").read_text(encoding="utf-8")
    ps1 = (ROOT / "scripts" / "Build-ProductionZip.ps1").read_text(encoding="utf-8")
    requirements = (ROOT / "scripts" / "production-build-requirements.txt").read_text(encoding="utf-8")
    source = MODULE_PATH.read_text(encoding="utf-8")

    require("Build-ProductionZip.ps1" in cmd, "root launcher must delegate to the PowerShell bootstrap")
    require("-3.10" in ps1 and "ROBOSTUDIO_BUILD_PYTHON" in ps1, "PowerShell bootstrap must auto-detect a supported build Python")
    require("ROBOSTUDIO_BUILD_CACHE" in ps1, "PowerShell bootstrap must own the production build cache root")
    require("Test-CacheCandidate" in ps1, "Windows production cache selection must verify writability")
    require("$env:PUBLIC" in ps1 and 'Join-Path $env:PUBLIC "RSC"' in ps1, "Windows production cache must prefer the short public profile path")
    require("must not contain spaces" in ps1, "Windows production cache override must reject whitespace paths")
    require("Clear-StalePlatformIOTemp" in ps1 and '".cache\\tmp"' in ps1, "PowerShell bootstrap must clean interrupted PlatformIO extraction temp state")
    require('$_ .Name' not in ps1, "PowerShell cache cleanup must not contain malformed member access")
    require('"pio-*"' in ps1 and '"platformio-*"' in ps1, "cache cleanup must cover both short and legacy PlatformIO cache names")
    require("Build cache :" in ps1, "PowerShell bootstrap must print the selected cache for diagnostics")
    require("pyinstaller" in requirements.lower() and "PySide6" in requirements, "build requirements must prepare the GUI freezer")
    for token in (
        "python-{PYTHON_RUNTIME_VERSION}-embed-amd64.zip",
        "PyInstaller",
        "platformio=={PLATFORMIO_CORE_VERSION}",
        '"pip>=24,<27"',
        "import platformio, yaml, pip",
        "_platformio_core_cache",
        'core_cache / "p"',
        '"platformio", "pkg", "install"',
        "_stage_esptool_python_runtime",
        "ESPTOOL_PACKAGE",
        "portable esptool runtime: PASS",
        '"-j", "1"',
        '"platformio", "run"',
        '"esp32dev"',
        "_probe_xtensa_toolchain",
        "_purge_xtensa_toolchain",
        "[repair] cached Xtensa toolchain is unusable",
        '"target_profiles.json"',
        '"one_command_production_build.py"',
        '"RoboStudio-{version}-Windows.zip"',
    ):
        require(token in source, f"B2.7 orchestrator is missing required production stage: {token}")

    workflow = (ROOT / ".github" / "workflows" / "robotics-ci.yml").read_text(encoding="utf-8")
    require("Run B2.7 full Windows production ZIP build" in workflow, "CI must exercise the real one-click production build")
    require("BUILD_PRODUCTION_ZIP.cmd --clean" in workflow, "CI must run the same production launcher used by Windows operators")

    print("B2.7 one-click production ZIP gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
