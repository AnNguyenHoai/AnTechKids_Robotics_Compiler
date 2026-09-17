"""RSD-21.7 real compiler integration regression suite."""
from __future__ import annotations
import json, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tests.support.production_fixture import make_production_inputs
from tools import production_distribution, production_e2e, release_package

def check(name: str, condition: bool) -> None:
    if not condition:raise AssertionError(name)
    print(f"PASS: {name}")

def _make_app(path: Path) -> None:
    path.write_text("import sys\nif '--self-test' in sys.argv:\n print('ROBOSTUDIO_E2E_READY')\n raise SystemExit(0)\nraise SystemExit(0)\n",encoding="utf-8")

def main() -> int:
    compiler_root=ROOT/"robot-compiler"; frontend_root=ROOT/"robot-frontend-robosim"/"frontend"
    check("real compiler source exists",(compiler_root/"main.py").is_file())
    check("real RoboSim frontend exists",(frontend_root/"rewriter.py").is_file())
    with tempfile.TemporaryDirectory(prefix="rsd-21-7-test-") as td:
        base=Path(td); inputs=make_production_inputs(base,compiler_root=compiler_root,frontend_root=frontend_root); _make_app(inputs.executable); dist=base/"distribution"
        result=production_distribution.build_production_distribution(inputs,dist); manifest=json.loads(result.manifest.read_text(encoding="utf-8"))
        check("production distribution is created",dist.is_dir()); check("production distribution contains real compiler entry",(dist/"compiler"/"main.py").is_file()); check("production distribution contains frontend",(dist/"compiler"/"frontend"/"rewriter.py").is_file()); check("compiler is recorded",manifest["compiler"]=="compiler/main.py"); check("contract is recorded",manifest["compiler_contract"]=="compiler/robostudio_bridge.py"); check("bundled Python is packaged",(dist/"runtime"/"bin"/"python.exe").is_file()); check("bundled PlatformIO is packaged",(dist/"runtime"/"platformio"/"platforms").is_dir() and (dist/"runtime"/"platformio"/"packages").is_dir()); check("runtime deployment manifest is packaged",(dist/"runtime"/"platformio"/"deployment-runtime.json").is_file()); check("production firmware is packaged",(dist/"firmware"/"robot-platform"/"platformio.ini").is_file())
        artifact=base/"release.zip"; release=release_package.build_release(dist,artifact)
        with zipfile.ZipFile(artifact) as archive:names=set(archive.namelist())
        check("ZIP contains compiler","compiler/main.py" in names); check("ZIP contains contract","compiler/robostudio_bridge.py" in names); check("ZIP contains frontend","compiler/frontend/rewriter.py" in names); check("ZIP contains bundled Python","runtime/bin/python.exe" in names); check("ZIP contains bundled PlatformIO",any(name.startswith("runtime/platformio/platforms/") for name in names)); check("ZIP contains production firmware",any(name.startswith("firmware/robot-platform/") for name in names)); check("ZIP validates",release_package.validate_release_artifact(artifact,release.manifest)["production_boundary"] is True)
        source=base/"sample.py"; source.write_text("forward(50)\nwait(100)\nstop()\n",encoding="utf-8")
        result=production_e2e.evaluate_production_artifact(artifact=artifact,source=source,launch=True,launch_command=["{python}","{app}","--self-test"],compile_command=["{python}","{compiler}","--file","{source}","--output","{output}"])
        report=result.to_dict(); compiler_output=Path(report["evidence"]["compiler_output"]).as_posix() if report["evidence"]["compiler_output"] else None
        check("RoboStudio starts from extracted ZIP",report["robostudio_started"] is True); check("real compiler executes",report["compiler_succeeded"] is True); check("compiler output produced",compiler_output=="e2e-output/program.h"); check("E2E PASS",report["status"]=="PASS")
    print("RSD-21.7 Real Compiler Integration checks: PASS"); return 0
if __name__=="__main__":raise SystemExit(main())
