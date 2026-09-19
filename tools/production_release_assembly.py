"""Assemble the production RoboStudio release artifact."""
from __future__ import annotations
import argparse,json,os,re,subprocess,sys
from dataclasses import dataclass
from pathlib import Path
if __package__ in (None, ""):
    root=Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:sys.path.insert(0,str(root))
from tools import portable_release_proof,production_distribution,release_package,release_provenance
REPORT_NAME="release-assembly-report.json"; PROOF_REPORT_NAME="portable-release-proof.json"; REPORT_SCHEMA="antechkids.robostudio.production-release-assembly"; REPORT_SCHEMA_VERSION=4; _VERSION_RE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
class ProductionReleaseAssemblyError(RuntimeError):pass
@dataclass(frozen=True)
class ProductionReleaseInputs:
    executable:Path; runtime_resources:Path; version_file:Path; source_revision:str; runtime_bin:Path; runtime_platformio:Path; compiler_root:Path|None=None; frontend_root:Path|None=None; firmware_root:Path|None=None
def repository_root()->Path:return Path(__file__).resolve().parents[1]
def _default_compiler_root()->Path:return repository_root()/"robot-compiler"
def _default_frontend_root()->Path:return repository_root()/"robot-frontend-robosim"/"frontend"
def _default_firmware_root()->Path:return repository_root()/"robot-platform"
def _resolve(path:Path)->Path:return Path(path).expanduser().resolve()
def _require_file(path:Path,label:str)->Path:
    path=_resolve(path)
    if not path.is_file():raise ProductionReleaseAssemblyError(f"Missing {label}: {path}")
    return path
def _require_directory(path:Path,label:str)->Path:
    path=_resolve(path)
    if not path.is_dir():raise ProductionReleaseAssemblyError(f"Missing {label}: {path}")
    return path
def _read_version(path:Path)->str:
    value=_require_file(path,"application VERSION file").read_text(encoding="utf-8").strip()
    if not value or "\n" in value or "\r" in value or not _VERSION_RE.fullmatch(value):raise ProductionReleaseAssemblyError(f"Invalid application VERSION: {path}")
    return value
def _source_revision(explicit:str|None)->str:
    if explicit and explicit.strip():return explicit.strip()
    env=os.environ.get("RSD_SOURCE_REVISION","").strip()
    if env:return env
    try:r=subprocess.run(["git","rev-parse","HEAD"],cwd=repository_root(),check=True,capture_output=True,text=True)
    except (OSError,subprocess.CalledProcessError) as exc:raise ProductionReleaseAssemblyError("Source revision is required when Git is unavailable; pass --source-revision.") from exc
    if not r.stdout.strip():raise ProductionReleaseAssemblyError("Unable to determine source revision; pass --source-revision.")
    return r.stdout.strip()
def validate_inputs(inputs:ProductionReleaseInputs,output_root:Path)->str:
    _require_file(inputs.executable,"RoboStudio executable"); _require_directory(inputs.runtime_resources,"application resources"); _require_directory(inputs.runtime_bin,"application-owned portable Python"); _require_directory(inputs.runtime_platformio,"application-owned PlatformIO runtime")
    if not (_resolve(inputs.runtime_bin)/"python.exe").is_file():raise ProductionReleaseAssemblyError("Application-owned Python runtime must contain python.exe")
    if not (_resolve(inputs.runtime_bin)/"Lib"/"site-packages"/"platformio"/"__init__.py").is_file():raise ProductionReleaseAssemblyError("Application-owned Python runtime must contain platformio in Lib/site-packages")
    for directory in ("platforms","packages"):
        if not (_resolve(inputs.runtime_platformio)/directory).is_dir():raise ProductionReleaseAssemblyError(f"Application-owned PlatformIO runtime is missing {directory}")
    compiler=_require_directory(inputs.compiler_root or _default_compiler_root(),"application-owned compiler"); frontend=_require_directory(inputs.frontend_root or _default_frontend_root(),"RoboSim frontend"); firmware=_require_directory(inputs.firmware_root or _default_firmware_root(),"application-owned firmware project")
    if not (compiler/"main.py").is_file() or not (compiler/"compiler").is_dir():raise ProductionReleaseAssemblyError("Invalid application-owned compiler: must contain main.py and compiler/")
    if not (frontend/"__init__.py").is_file() or not (frontend/"rewriter.py").is_file():raise ProductionReleaseAssemblyError("RoboSim frontend must contain __init__.py and rewriter.py")
    if not (firmware/"platformio.ini").is_file() or not (firmware/"wifi_config.py").is_file() or not (firmware/"main").is_dir():raise ProductionReleaseAssemblyError("Production firmware project must contain platformio.ini, wifi_config.py, and main/")
    version=_read_version(inputs.version_file); output_root=_resolve(output_root)
    for source in (_resolve(inputs.executable).parent,_resolve(inputs.runtime_resources),_resolve(inputs.runtime_bin),_resolve(inputs.runtime_platformio),compiler,frontend,firmware):
        try:output_root.relative_to(source)
        except ValueError:continue
        raise ProductionReleaseAssemblyError(f"Release output must not be inside an input source: {output_root}")
    return version
def _proof_failure_message(proof:portable_release_proof.PortableReleaseProofReport)->str:
    if not proof.findings:return "Portable release proof failed; artifact is not release-ready."
    samples=[]
    for finding in proof.findings[:12]:
        samples.append(f"{finding.source}: {finding.dependency} ({finding.reason})")
    suffix="" if len(proof.findings)<=12 else f"; +{len(proof.findings)-12} more finding(s)"
    return "Portable release proof failed: " + "; ".join(samples) + suffix
def assemble_release(inputs:ProductionReleaseInputs,output_root:Path)->dict[str,object]:
    output_root=_resolve(output_root); version=validate_inputs(inputs,output_root); output_root.mkdir(parents=True,exist_ok=True); distribution_root=output_root/"RoboStudio"; artifact=output_root/f"RoboStudio-{version}-Windows.zip"; proof_report=output_root/PROOF_REPORT_NAME; report_path=output_root/REPORT_NAME
    compiler_root=inputs.compiler_root or _default_compiler_root(); frontend_root=inputs.frontend_root or _default_frontend_root(); firmware_root=inputs.firmware_root or _default_firmware_root()
    try:
        distribution=production_distribution.build_production_distribution(production_distribution.ProductionDistributionInputs(_resolve(inputs.executable),_resolve(inputs.runtime_resources),_resolve(inputs.version_file),_resolve(inputs.runtime_bin),_resolve(inputs.runtime_platformio),_resolve(compiler_root),_resolve(frontend_root),_resolve(firmware_root)),distribution_root)
        release=release_package.build_release(distribution.distribution_root,artifact); provenance=release_provenance.write_provenance(distribution.distribution_root,release.manifest,release.artifact,artifact.with_name(release_provenance.PROVENANCE_MANIFEST),source_revision=inputs.source_revision); proof=portable_release_proof.prove_portable_release(release.artifact,manifest=release.manifest)
        proof_payload=portable_release_proof.report_to_dict(proof); proof_report.write_text(json.dumps(proof_payload,indent=2)+"\n",encoding="utf-8")
        if not proof.passed:raise ProductionReleaseAssemblyError(_proof_failure_message(proof))
        report={"schema":REPORT_SCHEMA,"schema_version":REPORT_SCHEMA_VERSION,"status":"PASS","portable":True,"runtime_model":"application-owned","target_machine_host_toolchain_required":False,"artifact_model":"RoboStudio + Compiler + Application-Owned Runtime","host_prerequisites_packaged":True,"compiler":"compiler/main.py","compiler_contract":"compiler/robostudio_bridge.py","frontend":"compiler/frontend","firmware":"firmware/robot-platform","bundled_python":"runtime/bin/python.exe","bundled_platformio":"runtime/platformio","application":distribution.application,"application_version":distribution.application_version,"source_revision":inputs.source_revision,"distribution":str(distribution.distribution_root),"artifact":str(release.artifact),"artifact_sha256":release.sha256,"release_manifest":str(release.manifest),"release_provenance":str(provenance),"portable_proof_report":str(proof_report),"proof":proof_payload}; report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); return report
    except Exception as exc:
        if isinstance(exc,ProductionReleaseAssemblyError):raise
        raise ProductionReleaseAssemblyError(str(exc)) from exc
def main()->int:
    p=argparse.ArgumentParser(description="Build a production RoboStudio release with application-owned Python, PlatformIO, compiler, RoboSim frontend, and firmware project"); p.add_argument("--executable",required=True,type=Path); p.add_argument("--runtime-bin",required=True,type=Path); p.add_argument("--runtime-platformio",required=True,type=Path); p.add_argument("--frontend-root",type=Path); p.add_argument("--compiler-root",type=Path); p.add_argument("--firmware-root",type=Path); p.add_argument("--runtime-resources",required=True,type=Path); p.add_argument("--version-file",type=Path,default=repository_root()/"VERSION"); p.add_argument("--source-revision",type=str); p.add_argument("--output",type=Path,default=repository_root()/"releases"/"production"); a=p.parse_args()
    try:r=assemble_release(ProductionReleaseInputs(a.executable,a.runtime_resources,a.version_file,_source_revision(a.source_revision),a.runtime_bin,a.runtime_platformio,a.compiler_root,a.frontend_root,a.firmware_root),a.output)
    except ProductionReleaseAssemblyError as exc:print(f"RSD-25 production release assembly: FAIL: {exc}",file=sys.stderr);return 1
    print("RSD-25 production release assembly: PASS");print(f"Artifact: {r['artifact']}");print(f"SHA-256: {r['artifact_sha256']}");print("Bundled Python: runtime/bin/python.exe");print("Bundled PlatformIO: runtime/platformio");print("Firmware: firmware/robot-platform");return 0
if __name__=="__main__":raise SystemExit(main())
