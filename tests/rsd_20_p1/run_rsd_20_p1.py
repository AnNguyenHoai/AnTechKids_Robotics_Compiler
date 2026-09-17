"""RSD-20-P.1 production release artifact assembly tests."""
from __future__ import annotations
import json, os, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from tools import production_release_assembly

def check(name:str,condition:bool)->None:
    if not condition:raise AssertionError(name)
    print(f"PASS: {name}")

def expect_error(name:str,fn,expected:str)->None:
    try:fn()
    except production_release_assembly.ProductionReleaseAssemblyError as exc:check(name,expected in str(exc))
    else:raise AssertionError(f"{name}: validation unexpectedly succeeded")

def make_inputs(root:Path)->production_release_assembly.ProductionReleaseInputs:
    executable=root/"upstream-build"/"RoboStudio.exe"; executable.parent.mkdir(parents=True); executable.write_bytes(b"production-executable")
    version=root/"VERSION"; version.write_text("7.2.0\n",encoding="utf-8")
    runtime_bin=root/"portable-python"; (runtime_bin/"Lib"/"site-packages"/"platformio").mkdir(parents=True); (runtime_bin/"python.exe").write_bytes(b"portable-python"); (runtime_bin/"Lib"/"site-packages"/"platformio"/"__init__.py").write_text("__version__='fixture'\n",encoding="utf-8")
    platformio=root/"platformio-runtime"; (platformio/"platforms"/"espressif32").mkdir(parents=True); (platformio/"packages"/"tool-esptoolpy").mkdir(parents=True); (platformio/"deployment-runtime.json").write_text(json.dumps({"schema":"antechkids.robostudio.deployment-runtime","schema_version":1,"portable_python_required":True,"host_virtualenv_included":False,"runtime_layout":{"core_dir":"runtime/platformio","python":"runtime/bin/python.exe"},"platformio_core":{"required_directories":["platforms","packages"]}})+"\n",encoding="utf-8")
    resources=root/"resources"; profile=resources/"robot-isa"/"target_profiles.json"; profile.parent.mkdir(parents=True); profile.write_text('{"targets": []}\n',encoding="utf-8")
    from tools import runtime_resources; runtime_resources.write_resource_manifest(resources)
    compiler=root/"compiler"; (compiler/"compiler").mkdir(parents=True); (compiler/"main.py").write_text("print('fixture')\n",encoding="utf-8"); (compiler/"robostudio_bridge.py").write_text("print('fixture')\n",encoding="utf-8")
    frontend=root/"frontend"; frontend.mkdir(); (frontend/"__init__.py").write_text("\n",encoding="utf-8"); (frontend/"rewriter.py").write_text("\n",encoding="utf-8")
    return production_release_assembly.ProductionReleaseInputs(executable=executable,runtime_bin=runtime_bin,runtime_platformio=platformio,runtime_resources=resources,version_file=version,source_revision="test-revision",compiler_root=compiler,frontend_root=frontend)

def main()->int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd20p1-") as temp:
        root=Path(temp); inputs=make_inputs(root); output=root/"release-output"; old_cwd=Path.cwd(); os.chdir(root)
        try:report=production_release_assembly.assemble_release(inputs,output)
        finally:os.chdir(old_cwd)
        artifact=output/"RoboStudio-7.2.0-Windows.zip"; check("production release artifact is created",artifact.is_file()); check("release artifact has non-zero size",artifact.stat().st_size>0); check("release manifest is created",(output/"release-manifest.json").is_file()); check("provenance sidecar is created",(output/"release-provenance.json").is_file()); check("portable proof report is created",(output/"portable-release-proof.json").is_file()); check("assembly report is created",(output/"release-assembly-report.json").is_file()); check("assembly report is PASS",report["status"]=="PASS"); check("assembly report records source revision",report["source_revision"]=="test-revision"); check("assembly report records artifact SHA-256",len(report["artifact_sha256"])==64)
        manifest=json.loads((output/"release-manifest.json").read_text(encoding="utf-8")); check("release is declared portable",manifest["portable"] is True); check("release version is deterministic",manifest["application_version"]=="7.2.0")
        missing=production_release_assembly.ProductionReleaseInputs(executable=root/"missing.exe",runtime_bin=inputs.runtime_bin,runtime_platformio=inputs.runtime_platformio,runtime_resources=inputs.runtime_resources,version_file=inputs.version_file,source_revision=inputs.source_revision,compiler_root=inputs.compiler_root,frontend_root=inputs.frontend_root)
        expect_error("missing executable is rejected before assembly",lambda:production_release_assembly.assemble_release(missing,root/"bad-output"),"RoboStudio executable")
        invalid_version=root/"bad-version"; invalid_version.write_text("7.2.0/evil\n",encoding="utf-8"); bad=production_release_assembly.ProductionReleaseInputs(executable=inputs.executable,runtime_bin=inputs.runtime_bin,runtime_platformio=inputs.runtime_platformio,runtime_resources=inputs.runtime_resources,version_file=invalid_version,source_revision=inputs.source_revision,compiler_root=inputs.compiler_root,frontend_root=inputs.frontend_root)
        expect_error("unsafe version is rejected",lambda:production_release_assembly.assemble_release(bad,root/"bad-version-output"),"Invalid application VERSION")
    print("RSD-20-P.1 production release assembly checks: PASS"); return 0
if __name__=="__main__":raise SystemExit(main())
