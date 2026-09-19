"""RSD-21.8 — real RoboStudio ↔ Compiler contract regression."""
from __future__ import annotations
import json, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
ROBOSTUDIO_ROOT=ROOT/"robostudio"
if str(ROBOSTUDIO_ROOT) not in sys.path:sys.path.insert(0,str(ROBOSTUDIO_ROOT))
from tools import production_distribution, release_package
from services.build_worker import BuildWorker

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
    runtime_bin=root/"python-runtime"
    (runtime_bin/"Lib"/"encodings").mkdir(parents=True)
    (runtime_bin/"Lib"/"site-packages"/"platformio").mkdir(parents=True)
    (runtime_bin/"python.exe").write_bytes(b"portable-python")
    (runtime_bin/"python310.dll").write_bytes(b"portable-python-runtime")
    (runtime_bin/"Lib"/"encodings"/"__init__.py").write_text("# fixture stdlib bootstrap\n",encoding="utf-8")
    (runtime_bin/"Lib"/"site-packages"/"platformio"/"__init__.py").write_text("__version__='fixture'\n",encoding="utf-8")
    runtime_platformio=root/"platformio-runtime"; platform=runtime_platformio/"platforms"/"espressif32"; platform.mkdir(parents=True)
    (platform/"platform.json").write_text(json.dumps({"name":"espressif32","version":"6.12.0","frameworks":{"arduino":{"package":"framework-arduinoespressif32"}},"packages":{"toolchain-xtensa-esp32":{"version":">=1.0.0"},"framework-arduinoespressif32":{"version":"1.0.0"}}},indent=2)+"\n",encoding="utf-8")
    toolchain=runtime_platformio/"packages"/"toolchain-xtensa-esp32"; toolchain.mkdir(parents=True); (toolchain/"package.json").write_text('{"name":"toolchain-xtensa-esp32","version":"1.2.0","dependencies":{}}\n',encoding="utf-8")
    framework=runtime_platformio/"packages"/"framework-arduinoespressif32"; framework.mkdir(parents=True); (framework/"package.json").write_text('{"name":"framework-arduinoespressif32","version":"1.0.0","dependencies":{}}\n',encoding="utf-8")
    (runtime_platformio/"deployment-runtime.json").write_text(json.dumps({"schema":"antechkids.robostudio.deployment-runtime","schema_version":1,"platformio_core":{"source_not_embedded":True,"required_directories":["platforms","packages"],"file_count":0},"runtime_layout":{"core_dir":"runtime/platformio","python":"runtime/bin/python.exe","platformio_module":"platformio"},"portable_python_required":True,"host_virtualenv_included":False},indent=2)+"\n",encoding="utf-8")
    return runtime_bin,runtime_platformio

def _run_contract(name,bridge,source,out,report,request,cwd):
    request.write_text(json.dumps({"source":str(source),"output":str(out),"report":str(report),"source_kind":"robosim-python"}),encoding="utf-8")
    proc=subprocess.run([sys.executable,str(bridge),"--request",str(request)],cwd=cwd,text=True,capture_output=True)
    check(f"{name} contract process succeeds",proc.returncode==0)
    if proc.returncode!=0:
        raise AssertionError(f"{name} contract failed:\nstdout={proc.stdout}\nstderr={proc.stderr}")
    payload=json.loads(proc.stdout)
    check(f"{name} contract schema is stable",payload["schema"]=="antechkids.robostudio.compiler-contract")
    check(f"{name} contract version is stable",payload["contract_version"]==1)
    check(f"{name} contract returns PASS",payload["status"]=="PASS")
    check(f"{name} compiler output exists",out.is_file() and out.stat().st_size>0)
    check(f"{name} contract report exists",report.is_file())
    check(f"{name} report records source kind",json.loads(report.read_text(encoding="utf-8"))["source_kind"]=="robosim-python")
    return payload,proc.stdout

def _check_human_log(contract_stdout,payload):
    details,summary=BuildWorker.format_result(contract_stdout,"",True)
    check("compiler contract JSON is hidden from user log",details=="")
    check("compile summary reports success","Compile successful" in summary)
    check("compile summary reports instruction count",f"Instructions: {payload['instruction_count']}" in summary)
    check("compile summary hides temporary paths","robostudio-compile-" not in summary and "rewritten_source" not in summary)
    check("compile summary does not claim Arduino build","Arduino" not in summary and "upload" not in summary.lower())

    fail_stdout=json.dumps({
        "schema":"antechkids.robostudio.compiler-contract",
        "contract_version":1,
        "status":"FAIL",
        "source_kind":"robosim-python",
        "source":"C:/Temp/robostudio-compile-x/program.py",
        "rewritten_source":None,
        "output":None,
        "report":None,
        "instruction_count":0,
        "error_code":"INVALID_SOURCE",
        "error_message":"example syntax error",
    },indent=2)
    fail_details,fail_summary=BuildWorker.format_result(fail_stdout,"",False)
    check("failed contract JSON is hidden from user log",fail_details=="")
    check("failed summary preserves error code","INVALID_SOURCE" in fail_summary)
    check("failed summary preserves useful error message","example syntax error" in fail_summary)

def main():
    compiler_root=ROOT/"robot-compiler"; frontend_root=ROOT/"robot-frontend-robosim"/"frontend"
    check("real compiler entry exists",(compiler_root/"main.py").is_file())
    check("real RoboSim frontend exists",(frontend_root/"rewriter.py").is_file())
    source_bridge=compiler_root/"compiler"/"robostudio_bridge.py"
    check("source contract endpoint exists",source_bridge.is_file())
    with tempfile.TemporaryDirectory(prefix="rsd-21-8-") as td:
        base=Path(td)
        source=base/"student.py"; source.write_text("import rcu\nrcu.SetMoveSpeed(50, 80)\nrcu.SetWaitForTime(1)\n",encoding="utf-8")

        # Reproduce RoboStudio's source-checkout invocation from an unrelated cwd.
        # This guards against compiler.py shadowing the compiler package and also
        # proves that the sibling RoboSim frontend is discovered without PYTHONPATH.
        source_cwd=base/"source-cwd"; source_cwd.mkdir()
        source_payload,source_stdout=_run_contract("source layout",source_bridge,source,base/"source-program.h",base/"source-contract.json",base/"source-request.json",source_cwd)
        _check_human_log(source_stdout,source_payload)

        inputs=base/"inputs"; inputs.mkdir(); exe=inputs/"RoboStudio.exe"; exe.write_bytes(b"fixture")
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
        check("bundled Python runtime DLL packaged",any((dist/"runtime"/"bin").glob("python*.dll")))
        check("bundled Python stdlib bootstrap packaged",(dist/"runtime"/"bin"/"Lib"/"encodings"/"__init__.py").is_file())
        check("bundled PlatformIO packaged",(dist/"runtime"/"platformio"/"platforms").is_dir())
        check("manifest records contract",manifest["compiler_contract"]=="compiler/robostudio_bridge.py")
        artifact=base/"release.zip"; release=release_package.build_release(dist,artifact)
        check("production ZIP validates",release_package.validate_release_artifact(artifact,release.manifest)["production_boundary"] is True)
        with zipfile.ZipFile(artifact) as z:names=set(z.namelist())
        check("ZIP contains contract", "compiler/robostudio_bridge.py" in names)
        check("ZIP contains frontend", "compiler/frontend/rewriter.py" in names)
        check("ZIP contains firmware", "firmware/robot-platform/platformio.ini" in names)
        check("ZIP contains Python", "runtime/bin/python.exe" in names)
        check("ZIP contains Python runtime DLL", any(name.startswith("runtime/bin/python") and name.endswith(".dll") for name in names))
        check("ZIP contains PlatformIO", "runtime/platformio/platforms/espressif32/" in names or any(n.startswith("runtime/platformio/platforms/espressif32/") for n in names))

        extracted=base/"extracted"; extracted.mkdir()
        with zipfile.ZipFile(artifact) as z:z.extractall(extracted)
        packaged_bridge=extracted/"compiler"/"robostudio_bridge.py"
        packaged_out=base/"program.h"; packaged_report=base/"contract.json"
        _run_contract("packaged layout",packaged_bridge,source,packaged_out,packaged_report,base/"request.json",extracted)
        check("compiled output contains generated program",len(packaged_out.read_text(encoding="utf-8"))>0)
    print("RSD-21.8 Real RoboStudio ↔ Compiler Contract checks: PASS")
    return 0
if __name__=="__main__":raise SystemExit(main())
