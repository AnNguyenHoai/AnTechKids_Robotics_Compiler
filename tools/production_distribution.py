"""Build a production RoboStudio distribution within the RSD-21 release boundary."""
from __future__ import annotations
import argparse, shutil, sys, tempfile
from dataclasses import dataclass
from pathlib import Path
if __package__ in (None, ""):
    _repository_root=Path(__file__).resolve().parent.parent
    if str(_repository_root) not in sys.path: sys.path.insert(0,str(_repository_root))
from tools import distribution_package
PRODUCTION_SCHEMA="antechkids.robostudio.production-distribution"; PRODUCTION_SCHEMA_VERSION=2; DEFAULT_VERSION_FILE="VERSION"; LAUNCHER_NAME="RoboStudio.cmd"; COMPILER_ROOT_NAME="compiler"; COMPILER_ENTRY_NAME="main.py"; FRONTEND_ROOT_NAME="frontend"; CONTRACT_ENTRY_NAME="robostudio_bridge.py"
class ProductionDistributionError(RuntimeError): pass
@dataclass(frozen=True)
class ProductionDistributionInputs:
    executable:Path
    runtime_resources:Path
    version_file:Path
    compiler_root:Path|None=None
    frontend_root:Path|None=None
@dataclass(frozen=True)
class ProductionDistributionResult:
    distribution_root:Path; manifest:Path; application:str; application_version:str

def repository_root()->Path:return Path(__file__).resolve().parents[1]
def _require_file(path:Path,label:str)->Path:
    path=Path(path).expanduser().resolve()
    if not path.is_file():raise ProductionDistributionError(f"Missing {label}: {path}")
    return path
def _require_directory(path:Path,label:str)->Path:
    path=Path(path).expanduser().resolve()
    if not path.is_dir():raise ProductionDistributionError(f"Missing {label}: {path}")
    return path
def _read_version(path:Path)->str:
    value=_require_file(path,"application VERSION file").read_text(encoding="utf-8").strip()
    if not value or "\n" in value or "\r" in value:raise ProductionDistributionError(f"Invalid application VERSION: {path}")
    return value
def validate_inputs(inputs:ProductionDistributionInputs,output:Path|None=None)->str:
    executable=_require_file(inputs.executable,"RoboStudio executable"); resources=_require_directory(inputs.runtime_resources,"application resources"); version=_read_version(inputs.version_file)
    compiler=_require_directory(inputs.compiler_root,"application-owned compiler")
    if not (compiler/COMPILER_ENTRY_NAME).is_file() or not (compiler/"compiler").is_dir():raise ProductionDistributionError("Invalid application-owned compiler: must contain main.py and compiler/")
    contract=compiler/"compiler"/CONTRACT_ENTRY_NAME
    if not contract.is_file():raise ProductionDistributionError(f"Application-owned compiler contract is missing: {contract}")
    frontend=_require_directory(inputs.frontend_root,"RoboSim frontend")
    if not (frontend/"__init__.py").is_file() or not (frontend/"rewriter.py").is_file():raise ProductionDistributionError("RoboSim frontend must contain __init__.py and rewriter.py")
    if output is not None:
        output=Path(output).expanduser().resolve()
        for source in (executable.parent,resources,compiler,frontend):
            try:output.relative_to(source)
            except ValueError:continue
            raise ProductionDistributionError(f"Distribution output must not be inside an input source: {output}")
    return version
def _launcher_text(executable_name:str)->str:
    return '@echo off\r\nsetlocal\r\npushd "%~dp0"\r\n' + f'if not exist "{executable_name}" (\r\n  echo RoboStudio executable not found: "%~dp0{executable_name}" 1>&2\r\n  popd\r\n  exit /b 1\r\n)\r\n"%~dp0{executable_name}" %*\r\nset "exit_code=%ERRORLEVEL%"\r\npopd\r\nexit /b %exit_code%\r\n'
def _stage_application(executable:Path,version_file:Path,stage:Path)->Path:
    stage.mkdir(parents=True,exist_ok=True); staged=stage/executable.name; shutil.copy2(executable,staged); shutil.copy2(version_file,stage/DEFAULT_VERSION_FILE); (stage/LAUNCHER_NAME).write_text(_launcher_text(executable.name),encoding="utf-8")
    for dependency in sorted(executable.parent.glob("*.dll"),key=lambda item:item.name.lower()):
        if dependency.is_file():shutil.copy2(dependency,stage/dependency.name)
    return staged
def _stage_compiler(compiler_root:Path,frontend_root:Path,stage:Path)->tuple[Path,Path]:
    compiler=_require_directory(compiler_root,"application-owned compiler"); frontend=_require_directory(frontend_root,"RoboSim frontend"); destination=stage/COMPILER_ROOT_NAME
    shutil.copytree(compiler,destination,ignore=shutil.ignore_patterns("__pycache__",".pytest_cache",".git",".venv",".pio","penv",CONTRACT_ENTRY_NAME))
    contract_source=compiler/"compiler"/CONTRACT_ENTRY_NAME
    if not contract_source.is_file():raise ProductionDistributionError(f"Application-owned compiler contract is missing: {contract_source}")
    shutil.copy2(contract_source,destination/CONTRACT_ENTRY_NAME)
    frontend_destination=destination/FRONTEND_ROOT_NAME; shutil.copytree(frontend,frontend_destination,ignore=shutil.ignore_patterns("__pycache__",".pytest_cache",".git",".venv",".pio","penv")); return destination,frontend_destination
def build_production_distribution(inputs:ProductionDistributionInputs,output:Path)->ProductionDistributionResult:
    output=Path(output).expanduser().resolve(); executable=Path(inputs.executable).expanduser().resolve(); version_file=Path(inputs.version_file).expanduser().resolve(); runtime_resources=Path(inputs.runtime_resources).expanduser().resolve(); validate_inputs(inputs,output); version=_read_version(version_file)
    with tempfile.TemporaryDirectory(prefix="robostudio-production-stage-") as temp:
        stage=Path(temp)/"application"; staged_executable=_stage_application(executable,version_file,stage); compiler_stage,_=_stage_compiler(Path(inputs.compiler_root),Path(inputs.frontend_root),stage)
        try:
            manifest=distribution_package.assemble_distribution(distribution_package.DistributionInputs(executable=staged_executable,runtime_resources=runtime_resources,production_boundary=True,launcher=stage/LAUNCHER_NAME,compiler_root=compiler_stage,frontend_root=None),output)
        except distribution_package.DistributionPackageError as exc:raise ProductionDistributionError(f"Production distribution assembly failed: {exc}") from exc
    return ProductionDistributionResult(output,manifest,executable.name,version)
def main()->int:
    parser=argparse.ArgumentParser(description="Assemble a production RoboStudio distribution with its real compiler contract"); parser.add_argument("--executable",required=True,type=Path); parser.add_argument("--compiler-root",required=True,type=Path); parser.add_argument("--frontend-root",required=True,type=Path); parser.add_argument("--runtime-resources",required=True,type=Path); parser.add_argument("--version-file",type=Path,default=repository_root()/DEFAULT_VERSION_FILE); parser.add_argument("--output",required=True,type=Path); args=parser.parse_args()
    try:r=build_production_distribution(ProductionDistributionInputs(args.executable,args.runtime_resources,args.version_file,args.compiler_root,args.frontend_root),args.output)
    except ProductionDistributionError as exc:print(f"RSD-21.8 production distribution: FAIL: {exc}",file=sys.stderr);return 1
    print("RSD-21.8 production distribution: PASS");print(f"Distribution: {r.distribution_root}");print(f"Manifest: {r.manifest}");print(f"Compiler: {r.distribution_root/COMPILER_ROOT_NAME/COMPILER_ENTRY_NAME}");print(f"Contract: {r.distribution_root/COMPILER_ROOT_NAME/CONTRACT_ENTRY_NAME}");return 0
if __name__=="__main__":raise SystemExit(main())
