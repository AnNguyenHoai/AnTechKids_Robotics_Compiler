"""RSD-21.5 production RoboStudio + Compiler E2E contract regression suite."""
from __future__ import annotations
import json, sys, tempfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools import production_e2e

def check(name: str, condition: bool) -> None:
    if not condition: raise AssertionError(name)
    print(f"PASS: {name}")

def _make_test_artifact(root: Path) -> tuple[Path, Path]:
    package=root/"package"; package.mkdir()
    app=package/"RoboStudio.exe"
    app.write_text("import sys\nargs=sys.argv[1:]\nif '--self-test' in args:\n    print('ROBOSTUDIO_E2E_READY')\n    raise SystemExit(0)\nraise SystemExit(2)\n",encoding="utf-8")
    compiler=package/"compiler"; compiler.mkdir()
    (compiler/"main.py").write_text("import pathlib, sys\nargs=sys.argv[1:]\nout=pathlib.Path(args[args.index('--output')+1])\nout.parent.mkdir(parents=True, exist_ok=True)\nout.write_bytes(b'ROBOT_BYTECODE_E2E_OK\\n')\nprint('COMPILER_E2E_OK')\n",encoding="utf-8")
    resources=package/"runtime"/"resources"; resources.mkdir(parents=True)
    (resources/"target_profiles.json").write_text('{"targets": []}\n',encoding="utf-8")
    artifact=root/"production.zip"
    with zipfile.ZipFile(artifact,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob("*")):
            if path.is_file(): archive.write(path,path.relative_to(package).as_posix())
    source=root/"sample.py"; source.write_text("forward(50)\nwait(100)\nstop()\n",encoding="utf-8")
    return artifact,source

def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-5-test-") as td:
        root=Path(td); artifact,source=_make_test_artifact(root)
        result=production_e2e.evaluate_production_artifact(artifact=artifact,source=source,launch=True,launch_command=[sys.executable,"{app}","--self-test"],compile_command=[sys.executable,"{compiler}","--source","{source}","--output","{output}"])
        report=result.to_dict(); names=set(zipfile.ZipFile(artifact).namelist())
        check("production artifact exists",artifact.is_file()); check("E2E report is JSON serializable",bool(json.dumps(report))); check("E2E status is PASS",report["status"]=="PASS"); check("target machine prerequisites remain external",report["target_machine_prerequisites"] is True); check("source tree is not executed",report["source_tree_execution"] is False); check("RoboStudio starts from extracted artifact",report["robostudio_started"] is True); check("compiler executes from extracted artifact",report["compiler_succeeded"] is True); check("extraction root is recorded",bool(report["extracted_root"])); check("RoboStudio executable is recorded",report["evidence"]["robostudio"]=="RoboStudio.exe"); check("compiler entry point is recorded",report["evidence"]["compiler"]=="compiler/main.py"); check("artifact contains RoboStudio","RoboStudio.exe" in names); check("artifact contains compiler","compiler/main.py" in names); check("artifact contains runtime resources","runtime/resources/target_profiles.json" in names); check("artifact does not bundle Python",not any("python" in name.lower() for name in names)); check("artifact does not bundle PlatformIO",not any("platformio" in name.lower() for name in names))
    print("RSD-21.5 RoboStudio + Compiler E2E checks: PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
