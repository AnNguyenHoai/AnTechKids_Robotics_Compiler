"""RSD-21.8 — real RoboStudio ↔ Compiler contract regression."""
from __future__ import annotations
import json, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools import production_distribution, release_package

def check(name,condition):
    if not condition:raise AssertionError(name)
    print(f"PASS: {name}")

def _make_firmware(root):
    firmware=root/"firmware"; (firmware/"main").mkdir(parents=True)
    (firmware/"platformio.ini").write_text("[platformio]\nsrc_dir = main\n\n[env:esp32dev]\nplatform = espressif32@6.12.0\nboard = esp32dev\nframework = arduino\n\n[env:esp32dev_ota]\nextends = env:esp32dev\nupload_protocol = espota\n\n[env:esp32dev_bootstrap]\nextends = env:esp32dev\n",encoding="utf-8")
    (firmware/"wifi_config.py").write_text("# clean production fixture\n",encoding="utf-8")
    (firmware/"main"/"main.cpp").write_text("void setup() {}\nvoid loop() {}\n",encoding="utf-8")
    return firmware

def _make_runtime(root):
    runtime_bin=root/"python-runtime"; (runtime_bin/"Lib"/"site-packages"/"platformio").mkdir(parents=True); (runtime_bin/"python.exe").write_bytes(b"portable-python"); (runtime_bin/"Lib"/"site-packages"/"platformio"/"__init__.py").write_text("__version__='fixture'\n",encoding="utf-8")
    runtime_platformio=root/"platformio-runtime"; platform=runtime_platformio/"platforms"/"espressif32"; platform.mkdir(parents=True)
    (platform/"platform.json").write_text(json.dumps({"name":"espressif32","version":"6.12.0","frameworks":{"arduino":{"package":"framework-arduinoespressif32"}},"packages":{"toolchain-xtensa-esp32":{"version":">=1.0.0"},"framework-arduinoespressif32":{"version":"1.0.0"}}},indent=2)+"\n",encoding="utf-8")
    toolchain=runtime_platformio/"packages"/"toolchain-xtensa-esp32"; toolchain.mkdir(parents=True); (toolchain/"package.json").write_text('{"name":"toolchain-xtensa-esp32","version":"1.2.0","dependencies":{}}\n',encoding="utf-8")
    framework=runtime_platformio/"packages"/"framework-arduinoespressif32"; framework.mkdir(parents=True); (framework/"package.json").write_text('{"name":"framework-arduinoespressif32","version":"1.0.0","dependencies":{}}\n',encoding="utf-8")
    (runtime_platformio/"deployment-runtime.json").write_text(json.dumps({"schema":"antechkids.robostudio.deployment-runtime","schema_version":1,"platformio_core":{"source_not_embedded":True,"required_directories":["platforms","packages"],"file_count":0},"runtime_layout":{"core_dir":"runtime/platformio","python":"runtime/bin/python.exe","platformio_module":"platformio"},"portable_python_required":True,"host_virtualenv_included":False},indent=2)+"\n",encoding="utf-8")
    return runtime_bin,runtime_platformio

def main():
    compiler_root=ROOT/"robot-compiler"; frontend_root=ROOT/"robot-frontend-robosim"/"frontend"
    check("real compiler entry exists",(compiler_root/"main.py").is_file())
    check("real RoboSim frontend exists",(frontend_root/"rewriter.py").is_file())
    with tempfile.TemporaryDirectory(prefix="rsd-21-8-") as td:
        base=Path(td); inputs=base/"inputs"; inputs.mkdir(); exe=inputs/"RoboStudio.exe"; exe.write_bytes(b"fixture")
        (inputs/"VERSION").write_text("1.2.3\n",encoding="utf-8")
        resources=inputs/"resources"; (resources/"robot-isa").mkdir(parents=True); (resources/"robot-isa"/"target_profiles.json").write_text('{"targets":[]}\n',encoding="utf-8")
        runtime_bin,runtime_platformio=_make_runtime(inputs)
        firmware=_make_firmware(inputs); dist=base/"dist"
        result=production_distribution.build_production_distribution(production_distribution.ProductionDistributionInputs(exe,resources,inputs/"VERSION",runtime_bin,runtime_platformio,compiler_root,frontend_root,firmware),dist)
        manifest=json.loads(result.manifest.read_text(encoding="utf-8"))
        check("contract endpoint packaged",(dist/"compiler"/"robostudio_bridge.py").is_file())
        check("frontend packaged",(dist/"compiler"/"frontend"/"rewriter.py").is_file())
        check("firmware packaged",(dist/"firmware"/"robot-platform"/"platformio.ini").is_file())
        check("bundled Python packaged",(dist/"runtime"/"bin"/"python.exe").is_file())
        check("bundled PlatformIO packaged",(dist/"runtime"/"platformio"/"platforms").is_dir())
        check("manifest records contract",manifest["compiler_contract"]=="compiler/robostudio_bridge.py")
        artifact=base/"release.zip"; release=release_package.build_release(dist,artifact)
        check("production ZIP validates",release_package.validate_release_artifact(artifact,release.manifest)["production_boundary"] is True)
        with zipfile.ZipFile(artifact) as z:names=set(z.namelist())
        check("ZIP contains contract", "compiler/robostudio_bridge.py" in names)
        check("ZIP contains frontend", "compiler/frontend/rewriter.py" in names)
        check("ZIP contains firmware", "firmware/robot-platform/platformio.ini" in names)
        check("ZIP contains Python", "runtime/bin/python.exe" in names)
        check("ZIP contains PlatformIO", "runtime/platformio/platforms/espressif32/" in names or any(n.startswith("runtime/platformio/platforms/espressif32/") for n in names))
        source=base/"student.py"; source.write_text("import rcu\nrcu.SetMoveSpeed(50, 80)\nrcu.SetWaitForTime(1)\n",encoding="utf-8")
        out=base/"program.h"; report=base/"contract.json"; extracted=base/"extracted"; extracted.mkdir()
        with zipfile.ZipFile(artifact) as z:z.extractall(extracted)
        bridge=extracted/"compiler"/"robostudio_bridge.py"; request=base/"request.json"; request.write_text(json.dumps({"source":str(source),"output":str(out),"report":str(report),"source_kind":"robosim-python"}),encoding="utf-8")
        proc=subprocess.run([sys.executable,str(bridge),"--request",str(request)],cwd=extracted,text=True,capture_output=True)
        check("contract process succeeds",proc.returncode==0)
        payload=json.loads(proc.stdout)
        check("contract schema is stable",payload["schema"]=="antechkids.robostudio.compiler-contract")
        check("contract version is stable",payload["contract_version"]==1)
        check("contract returns PASS",payload["status"]=="PASS")
        check("real compiler output exists",out.is_file() and out.stat().st_size>0)
        check("contract report exists",report.is_file())
        check("compiled output contains generated program",len(out.read_text(encoding="utf-8"))>0)
        check("report records source kind",json.loads(report.read_text(encoding="utf-8"))["source_kind"]=="robosim-python")
    print("RSD-21.8 Real RoboStudio ↔ Compiler Contract checks: PASS")
    return 0
if __name__=="__main__":raise SystemExit(main())
