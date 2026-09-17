"""Shared production-distribution fixture for release acceptance suites."""
from __future__ import annotations
import json
from pathlib import Path
from tools import production_distribution, runtime_resources

def make_production_inputs(root: Path, *, compiler_root: Path | None = None, frontend_root: Path | None = None) -> production_distribution.ProductionDistributionInputs:
    root = Path(root)
    executable = root / "app-build" / "RoboStudio.exe"; executable.parent.mkdir(parents=True, exist_ok=True); executable.write_bytes(b"production-executable")
    (executable.parent / "Qt6Core.dll").write_bytes(b"application-local-dll")
    version = root / "VERSION"; version.write_text("7.2.0\n", encoding="utf-8")
    compiler = compiler_root or root / "compiler"
    if compiler_root is None:
        (compiler / "compiler").mkdir(parents=True); (compiler / "main.py").write_text("print('compiler')\n", encoding="utf-8"); (compiler / "compiler" / "__init__.py").write_text("", encoding="utf-8"); (compiler / "robostudio_bridge.py").write_text("def compile_request(request):\n    return request\n", encoding="utf-8")
    frontend = frontend_root or root / "frontend"
    if frontend_root is None:
        frontend.mkdir(); (frontend / "__init__.py").write_text("", encoding="utf-8"); (frontend / "rewriter.py").write_text("def rewrite(source):\n    return source\n", encoding="utf-8")
    resources = root / "resources"; profile = resources / "robot-isa" / "target_profiles.json"; profile.parent.mkdir(parents=True); profile.write_text('{"targets": []}\n', encoding="utf-8"); runtime_resources.write_resource_manifest(resources)
    firmware = root / "firmware"; (firmware / "main").mkdir(parents=True); (firmware / "main" / "main.cpp").write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8"); (firmware / "wifi_config.py").write_text("Import('env')\n", encoding="utf-8")
    (firmware / "platformio.ini").write_text("[platformio]\nsrc_dir = main\n\n[env:esp32dev]\nplatform = espressif32@6.12.0\nboard = esp32dev\nframework = arduino\n\n[env:esp32dev_bootstrap]\nextends = env:esp32dev\n\n[env:esp32dev_ota]\nextends = env:esp32dev\nupload_protocol = espota\n", encoding="utf-8")
    runtime_bin = root / "runtime-bin"; (runtime_bin / "Lib" / "site-packages" / "platformio").mkdir(parents=True); (runtime_bin / "python.exe").write_bytes(b"portable-python"); (runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py").write_text("__version__ = 'test'\n", encoding="utf-8")
    runtime_platformio = root / "runtime-platformio"; platform = runtime_platformio / "platforms" / "espressif32"; platform.mkdir(parents=True); (runtime_platformio / "packages" / "toolchain-xtensa-esp32").mkdir(parents=True); (runtime_platformio / "packages" / "framework-arduinoespressif32").mkdir(parents=True)
    (platform / "platform.json").write_text(json.dumps({"name":"espressif32","version":"6.12.0","frameworks":{"arduino":{"package":"framework-arduinoespressif32"}},"packages":{"toolchain-xtensa-esp32":{"version":">=1.0.0"},"framework-arduinoespressif32":{"version":"1.0.0"}}})+"\n", encoding="utf-8")
    (runtime_platformio / "packages" / "toolchain-xtensa-esp32" / "package.json").write_text('{"name":"toolchain-xtensa-esp32","version":"1.2.0","dependencies":{}}\n', encoding="utf-8"); (runtime_platformio / "packages" / "framework-arduinoespressif32" / "package.json").write_text('{"name":"framework-arduinoespressif32","version":"1.0.0","dependencies":{}}\n', encoding="utf-8")
    (runtime_platformio / "deployment-runtime.json").write_text(json.dumps({"schema":"antechkids.robostudio.deployment-runtime","schema_version":1,"platformio_core":{"source_not_embedded":True,"required_directories":["platforms","packages"],"file_count":0},"runtime_layout":{"core_dir":"runtime/platformio","python":"runtime/bin/python.exe","platformio_module":"platformio"},"portable_python_required":True,"host_virtualenv_included":False})+"\n", encoding="utf-8")
    return production_distribution.ProductionDistributionInputs(executable=executable,runtime_resources=resources,version_file=version,runtime_bin=runtime_bin,runtime_platformio=runtime_platformio,compiler_root=compiler,frontend_root=frontend,firmware_root=firmware)
