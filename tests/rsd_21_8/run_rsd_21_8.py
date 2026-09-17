"""RSD-21.8 — real RoboStudio ↔ Compiler contract regression."""
from __future__ import annotations
import json, subprocess, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.support.production_fixture import make_production_inputs
from tools import production_distribution, release_package

def check(name,condition):
    if not condition:raise AssertionError(name)
    print(f"PASS: {name}")

def main():
    compiler_root=ROOT/"robot-compiler"; frontend_root=ROOT/"robot-frontend-robosim"/"frontend"
    check("real compiler entry exists",(compiler_root/"main.py").is_file()); check("real RoboSim frontend exists",(frontend_root/"rewriter.py").is_file())
    with tempfile.TemporaryDirectory(prefix="rsd-21-8-") as td:
        base=Path(td); inputs=make_production_inputs(base,compiler_root=compiler_root,frontend_root=frontend_root); dist=base/"dist"
        result=production_distribution.build_production_distribution(inputs,dist); manifest=json.loads(result.manifest.read_text(encoding="utf-8"))
        check("contract endpoint packaged",(dist/"compiler"/"robostudio_bridge.py").is_file()); check("frontend packaged",(dist/"compiler"/"frontend"/"rewriter.py").is_file()); check("bundled Python packaged",(dist/"runtime"/"bin"/"python.exe").is_file()); check("bundled PlatformIO packaged",(dist/"runtime"/"platformio"/"platforms").is_dir()); check("production firmware packaged",(dist/"firmware"/"robot-platform"/"platformio.ini").is_file()); check("manifest records contract",manifest["compiler_contract"]=="compiler/robostudio_bridge.py")
        artifact=base/"release.zip"; release=release_package.build_release(dist,artifact); check("production ZIP validates",release_package.validate_release_artifact(artifact,release.manifest)["production_boundary"] is True)
        with zipfile.ZipFile(artifact) as z:names=set(z.namelist())
        check("ZIP contains contract","compiler/robostudio_bridge.py" in names); check("ZIP contains frontend","compiler/frontend/rewriter.py" in names); check("ZIP contains Python","runtime/bin/python.exe" in names); check("ZIP contains PlatformIO",any(n.startswith("runtime/platformio/platforms/") for n in names)); check("ZIP contains firmware",any(n.startswith("firmware/robot-platform/") for n in names))
        source=base/"student.py"; source.write_text("import rcu\nrcu.SetMoveSpeed(50, 80)\nrcu.SetWaitForTime(1)\n",encoding="utf-8"); out=base/"program.h"; report=base/"contract.json"; extracted=base/"extracted"; extracted.mkdir()
        with zipfile.ZipFile(artifact) as z:z.extractall(extracted)
        bridge=extracted/"compiler"/"robostudio_bridge.py"; request=base/"request.json"; request.write_text(json.dumps({"source":str(source),"output":str(out),"report":str(report),"source_kind":"robosim-python"}),encoding="utf-8")
        proc=subprocess.run([sys.executable,str(bridge),"--request",str(request)],cwd=extracted,text=True,capture_output=True)
        check("contract process succeeds",proc.returncode==0); payload=json.loads(proc.stdout); check("contract schema is stable",payload["schema"]=="antechkids.robostudio.compiler-contract"); check("contract version is stable",payload["contract_version"]==1); check("contract returns PASS",payload["status"]=="PASS"); check("real compiler output exists",out.is_file() and out.stat().st_size>0); check("contract report exists",report.is_file()); check("compiled output contains generated program",len(out.read_text(encoding="utf-8"))>0); check("report records source kind",json.loads(report.read_text(encoding="utf-8"))["source_kind"]=="robosim-python")
    print("RSD-21.8 Real RoboStudio ↔ Compiler Contract checks: PASS"); return 0
if __name__=="__main__":raise SystemExit(main())
