"""Assemble and validate RoboStudio distribution payloads."""
from __future__ import annotations
import hashlib, json, shutil
from dataclasses import dataclass
from pathlib import Path
from tools import production_artifact_boundary, runtime_integrity, runtime_resources
DISTRIBUTION_MANIFEST="distribution-manifest.json"; SCHEMA="antechkids.robostudio.distribution"; SCHEMA_VERSION=2
class DistributionPackageError(RuntimeError): pass
@dataclass(frozen=True)
class DistributionInputs:
    executable: Path
    runtime_bin: Path|None=None
    runtime_platformio: Path|None=None
    runtime_resources: Path|None=None
    production_boundary: bool=False
    launcher: Path|None=None
    compiler_root: Path|None=None
    frontend_root: Path|None=None

def _copy_tree(source:Path,destination:Path,label:str)->None:
    if not source.is_dir(): raise DistributionPackageError(f"Missing distribution input {label}: {source}")
    destination.mkdir(parents=True,exist_ok=True)
    for item in source.iterdir():
        target=destination/item.name
        if item.is_dir():
            if item.name.lower() in {"penv",".venv",".pio"}: raise DistributionPackageError(f"Host-specific environment is not allowed: {item}")
            shutil.copytree(item,target,dirs_exist_ok=True)
        elif item.is_file(): shutil.copy2(item,target)

def _normalize_production_resources(destination:Path)->None:
    canonical=destination/"robot-isa"/"target_profiles.json"; legacy=destination/"target_profiles.json"
    if canonical.is_file():
        if legacy.exists():
            if legacy.is_dir(): raise DistributionPackageError("Conflicting production resource layouts: target_profiles.json")
            legacy.unlink()
    elif legacy.is_file(): canonical.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(legacy),str(canonical))

def _sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()

def _file_entries(root:Path)->list[dict[str,object]]:
    excluded={DISTRIBUTION_MANIFEST,production_artifact_boundary.BOUNDARY_MANIFEST}
    return [{"path":p.relative_to(root).as_posix(),"size":p.stat().st_size,"sha256":_sha256(p)} for p in sorted(root.rglob("*")) if p.is_file() and p.name not in excluded]

def _copy_application_metadata(executable:Path,output:Path)->None:
    version=executable.parent/runtime_integrity.APPLICATION_VERSION_FILE
    if version.is_file(): shutil.copy2(version,output/runtime_integrity.APPLICATION_VERSION_FILE)

def _copy_application_dependencies(executable:Path,output:Path)->None:
    for dependency in sorted(executable.parent.glob("*.dll"),key=lambda item:item.name.lower()):
        if dependency.is_file(): shutil.copy2(dependency,output/dependency.name)

def _copy_launcher(launcher:Path|None,output:Path)->None:
    if launcher is None:return
    launcher=Path(launcher).resolve()
    if not launcher.is_file(): raise DistributionPackageError(f"Missing production launcher: {launcher}")
    if launcher.suffix.lower() not in {".cmd",".bat"}: raise DistributionPackageError(f"Unsupported production launcher type: {launcher.name}")
    shutil.copy2(launcher,output/launcher.name)

def _copy_compiler(compiler_root:Path|None,frontend_root:Path|None,output:Path)->None:
    if compiler_root is None: raise DistributionPackageError("Production distribution requires application-owned compiler")
    source=Path(compiler_root).resolve()
    if not source.is_dir(): raise DistributionPackageError(f"Missing application-owned compiler: {source}")
    if not (source/"main.py").is_file() or not (source/"compiler").is_dir(): raise DistributionPackageError("Compiler root must contain main.py and compiler/")
    destination=output/"compiler"
    if destination.exists(): raise DistributionPackageError(f"Compiler destination already exists: {destination}")
    shutil.copytree(source,destination,ignore=shutil.ignore_patterns("__pycache__",".pytest_cache",".git",".venv",".pio","penv"))
    if frontend_root is not None:
        frontend=Path(frontend_root).resolve()
        if not frontend.is_dir(): raise DistributionPackageError(f"Missing RoboSim frontend: {frontend}")
        shutil.copytree(frontend,destination/"frontend",ignore=shutil.ignore_patterns("__pycache__",".pytest_cache",".git",".venv",".pio","penv"))

def _validate_legacy_runtime_inputs(inputs:DistributionInputs)->None:
    if inputs.runtime_bin is None or inputs.runtime_platformio is None or inputs.runtime_resources is None: raise DistributionPackageError("Legacy distribution assembly requires runtime_bin, runtime_platformio, and runtime_resources")

def assemble_distribution(inputs:DistributionInputs,output:Path)->Path:
    output=Path(output).resolve()
    if output.exists():
        if not output.is_dir(): raise DistributionPackageError(f"Distribution output is not a directory: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True); executable=Path(inputs.executable).resolve()
    if not executable.is_file(): raise DistributionPackageError(f"Missing RoboStudio executable: {executable}")
    shutil.copy2(executable,output/executable.name); _copy_application_dependencies(executable,output); _copy_application_metadata(executable,output)
    if inputs.production_boundary:
        if inputs.runtime_bin is not None or inputs.runtime_platformio is not None: raise DistributionPackageError("Production artifact boundary forbids bundled Python and PlatformIO inputs")
        if inputs.runtime_resources is None: raise DistributionPackageError("Production artifact assembly requires application resources")
        _copy_launcher(inputs.launcher,output); _copy_compiler(inputs.compiler_root,inputs.frontend_root,output)
        resource_output=output/"runtime"/"resources"; _copy_tree(Path(inputs.runtime_resources),resource_output,"application resources"); _normalize_production_resources(resource_output); runtime_resources.write_resource_manifest(resource_output)
        try: production_artifact_boundary.validate_distribution_root(output); production_artifact_boundary.write_boundary_manifest(output)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc: raise DistributionPackageError(f"Production artifact boundary validation failed: {exc}") from exc
        portable,runtime_root=False,"runtime"
    else:
        _validate_legacy_runtime_inputs(inputs); _copy_tree(Path(inputs.runtime_bin),output/"runtime"/"bin","portable Python"); _copy_tree(Path(inputs.runtime_platformio),output/"runtime"/"platformio","PlatformIO"); _copy_tree(Path(inputs.runtime_resources),output/"runtime"/"resources","runtime resources"); runtime_resources.write_resource_manifest(output/"runtime"/"resources")
        if not (output/"runtime"/"platformio"/"deployment-runtime.json").is_file(): raise DistributionPackageError("PlatformIO deployment manifest is missing")
        portable,runtime_root=True,"runtime"
        try:
            from tools import runtime_preflight; runtime_preflight.validate_distribution(output)
            runtime_integrity.write_runtime_manifest(output)
        except Exception as exc: raise DistributionPackageError(f"Assembled distribution runtime validation failed: {exc}") from exc
    manifest={"schema":SCHEMA,"schema_version":SCHEMA_VERSION,"application":executable.name,"portable":portable,"artifact_model":"RoboStudio + Compiler" if inputs.production_boundary else "legacy-runtime","runtime_root":runtime_root,"production_boundary":inputs.production_boundary,"compiler":"compiler/main.py" if inputs.production_boundary else None,"compiler_contract":"compiler/robostudio_bridge.py" if inputs.production_boundary else None,"frontend":"compiler/frontend" if inputs.production_boundary and inputs.frontend_root is not None else None,"files":_file_entries(output)}
    manifest_path=output/DISTRIBUTION_MANIFEST; manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8"); return manifest_path

def validate_distribution_manifest(path:Path)->dict:
    path=Path(path)
    try: manifest=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise DistributionPackageError(f"Invalid distribution manifest: {path}") from exc
    if manifest.get("schema")!=SCHEMA or manifest.get("schema_version")!=SCHEMA_VERSION: raise DistributionPackageError("Unsupported distribution manifest schema")
    root=path.parent
    for entry in manifest.get("files",[]):
        relative=Path(str(entry["path"]))
        if relative.is_absolute() or ".." in relative.parts: raise DistributionPackageError(f"Distribution manifest path escapes root: {relative}")
        actual=root/relative
        if not actual.is_file(): raise DistributionPackageError(f"Distribution file is missing: {relative.as_posix()}")
        if _sha256(actual)!=str(entry["sha256"]): raise DistributionPackageError(f"Distribution file checksum mismatch: {relative.as_posix()}")
        if actual.stat().st_size!=int(entry["size"]): raise DistributionPackageError(f"Distribution file size changed: {relative.as_posix()}")
    if manifest.get("production_boundary") is True:
        try: production_artifact_boundary.validate_distribution_root(root)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc: raise DistributionPackageError(f"Production artifact boundary validation failed: {exc}") from exc
        if manifest.get("artifact_model")!="RoboStudio + Compiler": raise DistributionPackageError("Production distribution has an invalid artifact model")
        for key in ("compiler","compiler_contract"):
            if manifest.get(key) and not (root/str(manifest[key])).is_file(): raise DistributionPackageError(f"Production distribution {key} is missing")
        if manifest.get("frontend") and not (root/str(manifest["frontend"])).is_dir(): raise DistributionPackageError("Production RoboSim frontend payload is missing")
    return manifest
