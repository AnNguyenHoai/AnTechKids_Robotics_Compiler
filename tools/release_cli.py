"""Canonical production release CLI for RoboStudio."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
if __package__ in (None,""):
    root=Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:sys.path.insert(0,str(root))
from tools import portable_release_proof,production_e2e,production_release_assembly,release_acceptance,release_package,target_machine_qualification

def _build_parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="python -m tools.release_cli",description="Build and verify a production RoboStudio release."); sub=p.add_subparsers(dest="command",required=True)
    b=sub.add_parser("build"); b.add_argument("--executable",required=True,type=Path); b.add_argument("--runtime-bin",required=True,type=Path); b.add_argument("--runtime-platformio",required=True,type=Path); b.add_argument("--compiler-root",type=Path); b.add_argument("--frontend-root",type=Path); b.add_argument("--runtime-resources",required=True,type=Path); b.add_argument("--version-file",type=Path,default=production_release_assembly.repository_root()/"VERSION"); b.add_argument("--source-revision"); b.add_argument("--output",type=Path,default=production_release_assembly.repository_root()/"releases"/"production"); b.add_argument("--json",action="store_true",dest="as_json")
    v=sub.add_parser("verify"); v.add_argument("artifact",type=Path); v.add_argument("--manifest",type=Path); v.add_argument("--json",action="store_true",dest="as_json")
    i=sub.add_parser("inspect"); i.add_argument("artifact",type=Path); i.add_argument("--manifest",type=Path); i.add_argument("--json",action="store_true",dest="as_json")
    a=sub.add_parser("accept"); a.add_argument("artifact",type=Path); a.add_argument("--timeout",type=float,default=30.0); a.add_argument("--report",type=Path); a.add_argument("--target-machine",action="store_true"); a.add_argument("--prerequisite-scope",choices=[s.value for s in target_machine_qualification.target_machine_prerequisites.RequirementScope],default="compile"); a.add_argument("--json",action="store_true",dest="as_json")
    e=sub.add_parser("e2e"); e.add_argument("artifact",type=Path); e.add_argument("--source",required=True,type=Path); e.add_argument("--launch-command",required=True); e.add_argument("--compile-command",required=True); e.add_argument("--timeout",type=float,default=production_e2e.DEFAULT_TIMEOUT); e.add_argument("--report",type=Path); e.add_argument("--json",action="store_true",dest="as_json")
    c=sub.add_parser("contract",help="execute the packaged RoboStudio -> Compiler contract"); c.add_argument("artifact",type=Path); c.add_argument("--source",required=True,type=Path); c.add_argument("--output",required=True,type=Path); c.add_argument("--report",type=Path); c.add_argument("--json",action="store_true",dest="as_json")
    return p

def _cmd_build(a):
    try:r=production_release_assembly.assemble_release(production_release_assembly.ProductionReleaseInputs(a.executable,a.runtime_resources,a.version_file,production_release_assembly._source_revision(a.source_revision),a.runtime_bin,a.runtime_platformio,a.compiler_root,a.frontend_root),a.output)
    except production_release_assembly.ProductionReleaseAssemblyError as exc:print(f"RSD-21.8 build: FAIL: {exc}",file=sys.stderr);return 1
    print(json.dumps(r,indent=2) if a.as_json else f"RSD-21.8 release: PASS\nArtifact: {r['artifact']}\nSHA-256: {r['artifact_sha256']}\nCompiler: {r['compiler']}\nContract: {r['compiler_contract']}");return 0

def _cmd_verify(a):
    try:r=portable_release_proof.prove_portable_release(a.artifact,manifest=a.manifest)
    except portable_release_proof.PortableReleaseProofError as exc:print(f"RSD-20 verify: FAIL: {exc}",file=sys.stderr);return 1
    payload=portable_release_proof.report_to_dict(r); print(json.dumps(payload,indent=2) if a.as_json else f"RSD-20 verify: {'PASS' if r.passed else 'FAIL'}\nArtifact: {r.artifact}\nSHA-256: {r.artifact_sha256}\nFiles: {r.file_count}\nPackaged dependencies: {r.packaged_dependency_count}"); return 0 if r.passed else 1

def _cmd_inspect(a):
    try:m=release_package.validate_release_artifact(a.artifact,a.manifest)
    except release_package.ReleasePackageError as exc:print(f"RSD-20 inspect: FAIL: {exc}",file=sys.stderr);return 1
    print(json.dumps(m,indent=2) if a.as_json else f"RSD-20 inspect: PASS\nArtifact: {a.artifact.resolve()}\nApplication: {m.get('application')}\nVersion: {m.get('application_version')}\nFiles: {m.get('file_count')}\nPortable: {m.get('portable')}");return 0

def _cmd_accept(a):
    if a.target_machine:
        try:r=target_machine_qualification.require_target_machine(scope=a.prerequisite_scope); payload=target_machine_qualification.to_dict(r); 
        except target_machine_qualification.TargetMachineQualificationError as exc:print(f"RSD-21.4 target-machine qualification: FAIL: {exc}",file=sys.stderr);return 1
        if a.report:target_machine_qualification.write_report(r,a.report)
        print(json.dumps(payload,indent=2) if a.as_json else f"RSD-21.4 target-machine qualification: PASS\nScope: {r.scope}");return 0
    try:r=release_acceptance.accept_release(a.artifact,timeout=a.timeout); ep=release_acceptance.write_evidence(r,a.report) if a.report else None
    except (release_acceptance.ReleaseAcceptanceError,OSError) as exc:print(f"RSD-20 accept: FAIL: {exc}",file=sys.stderr);return 1
    payload=release_acceptance.report_to_dict(r); print(json.dumps(payload,indent=2) if a.as_json else f"RSD-20 accept: PASS\nArtifact: {a.artifact}\nExecutable verified: {r.executable_verified}\nEnvironment verified: {r.environment_verified}"); return 0

def _cmd_e2e(a):
    try:r=production_e2e.qualify_release_e2e(a.artifact,source=a.source,launch_command=production_e2e.command_from_text(a.launch_command),compile_command=production_e2e.command_from_text(a.compile_command),timeout=a.timeout); payload=production_e2e.build_report(r)
    except production_e2e.ProductionE2EError as exc:print(f"RSD-21.7 E2E: FAIL: {exc}",file=sys.stderr);return 1
    if a.report:production_e2e.write_report(payload,a.report)
    print(json.dumps(payload,indent=2) if a.as_json else f"RSD-21.7 E2E: {payload['status']}\nRoboStudio started: {payload['robostudio_started']}\nCompiler succeeded: {payload['compiler_succeeded']}");return 0 if r.passed else 1

def _cmd_contract(a):
    import subprocess,tempfile,zipfile
    artifact=Path(a.artifact).resolve(); source=Path(a.source).resolve(); output=Path(a.output).resolve(); report=Path(a.report).resolve() if a.report else output.parent/"compile-contract-report.json"
    if not artifact.is_file() or not source.is_file(): print("RSD-21.8 contract: FAIL: artifact or source missing",file=sys.stderr);return 1
    with tempfile.TemporaryDirectory(prefix="robostudio-contract-") as td:
        root=Path(td); zipfile.ZipFile(artifact).extractall(root); candidates=list(root.rglob("compiler/robostudio_bridge.py"))
        if not candidates: print("RSD-21.8 contract: FAIL: packaged compiler contract missing",file=sys.stderr);return 1
        bridge=candidates[0]; request=root/"contract-request.json"; request.write_text(json.dumps({"source":str(source),"output":str(output),"report":str(report),"source_kind":"robosim-python"}),encoding="utf-8")
        proc=subprocess.run([sys.executable,str(bridge),"--request",str(request)],cwd=bridge.parent.parent,text=True,capture_output=True)
        if proc.returncode!=0: print(f"RSD-21.8 contract: FAIL: {proc.stdout or proc.stderr}",file=sys.stderr);return 1
        payload=json.loads(proc.stdout); ok=payload.get("status")=="PASS" and Path(payload.get("output","")).is_file() and payload.get("contract_version")==1
        if not ok: print("RSD-21.8 contract: FAIL: invalid compiler response",file=sys.stderr);return 1
        if a.report:report.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(payload,indent=2) if a.as_json else f"RSD-21.8 contract: PASS\nContract: {payload['schema']} v{payload['contract_version']}\nOutput: {payload['output']}\nInstructions: {payload['instruction_count']}");return 0

def main(argv=None):
    p=_build_parser();a=p.parse_args(argv); return {'build':_cmd_build,'verify':_cmd_verify,'inspect':_cmd_inspect,'accept':_cmd_accept,'e2e':_cmd_e2e,'contract':_cmd_contract}[a.command](a)
if __name__=="__main__":raise SystemExit(main())
