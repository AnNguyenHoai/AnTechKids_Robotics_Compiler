"""RSD-20-P production release proof and dependency-closure validation."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
if __package__ in (None, ""):
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
from tools import release_package, production_artifact_boundary

SCHEMA = "antechkids.robostudio.production-portable-release-proof"
SCHEMA_VERSION = 2
_RUNTIME_BIN = Path("runtime") / "bin"
_RUNTIME_PLATFORMIO = Path("runtime") / "platformio"
_RUNTIME_RESOURCES = Path("runtime") / "resources"
_SYSTEM_DLLS = {"advapi32.dll", "bcrypt.dll", "combase.dll", "comdlg32.dll", "crypt32.dll", "d3d9.dll", "dwmapi.dll", "gdi32.dll", "gdi32full.dll", "imm32.dll", "iphlpapi.dll", "kernel32.dll", "kernelbase.dll", "mpr.dll", "msimg32.dll", "msvcp_win.dll", "msvcrt.dll", "netapi32.dll", "ntdll.dll", "ole32.dll", "oleaut32.dll", "opengl32.dll", "powrprof.dll", "psapi.dll", "rpcrt4.dll", "secur32.dll", "shell32.dll", "shlwapi.dll", "user32.dll", "userenv.dll", "uxtheme.dll", "version.dll", "winhttp.dll", "wininet.dll", "winmm.dll", "winspool.drv", "ws2_32.dll", "wldap32.dll", "setupapi.dll", "cfgmgr32.dll", "comctl32.dll", "dxgi.dll", "d3d11.dll", "d3dcompiler_47.dll", "vcruntime140.dll", "vcruntime140_1.dll", "ucrtbase.dll"}
_SYSTEM_DLL_PREFIXES = ("api-ms-win-", "ext-ms-win-")

# Detect real host-owned absolute roots without treating an ordinary path segment
# or URL segment named "home"/"users" as a leak.  The negative look-behind
# requires the slash to begin a path token (start of string or punctuation), so
# both ``runtime/.../platformio/home/...`` and ``https://host/home/...`` remain
# valid while ``/home/alice/...`` and ``/Users/alice/...`` are still rejected.
_HOST_PATH_PATTERNS = (
    re.compile(rb"(?i)[a-z]:[\\/]+users[\\/]+"),
    re.compile(rb"(?i)[a-z]:[\\/]+program files[\\/]+(?:python|platformio)"),
    re.compile(rb"(?i)[a-z]:[\\/]+programdata[\\/]+platformio"),
    re.compile(rb"(?i)[a-z]:[\\/]+(?:\.platformio|pypoetry)"),
    re.compile(rb"(?i)(?<![A-Za-z0-9._~:/\\-])[\\/](?:home|users)[\\/]+"),
)
_TEXT_EXTENSIONS = (".json", ".txt", ".cfg", ".ini", ".toml", ".yaml", ".yml")

class PortableReleaseProofError(RuntimeError):
    pass

@dataclass(frozen=True)
class DependencyFinding:
    source: str
    dependency: str
    reason: str

@dataclass(frozen=True)
class PortableReleaseProofReport:
    artifact: Path
    application: str
    application_version: str
    artifact_sha256: str
    file_count: int
    runtime_python: str
    dependency_count: int
    system_dependency_count: int
    packaged_dependency_count: int
    findings: tuple[DependencyFinding, ...] = field(default_factory=tuple)
    passed: bool = True

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _is_system_dependency(name: str) -> bool:
    name = name.lower()
    return name in _SYSTEM_DLLS or name.startswith(_SYSTEM_DLL_PREFIXES)

def _rva_to_offset(data: bytes, rva: int) -> int | None:
    if len(data) < 0x40 or data[:2] != b"MZ": return None
    pe = int.from_bytes(data[0x3C:0x40], "little")
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\0\0": return None
    count = int.from_bytes(data[pe + 6:pe + 8], "little")
    opt_size = int.from_bytes(data[pe + 20:pe + 22], "little")
    table = pe + 24 + opt_size
    for i in range(count):
        section = table + i * 40
        if section + 40 > len(data): return None
        vsize = int.from_bytes(data[section + 8:section + 12], "little")
        vaddr = int.from_bytes(data[section + 12:section + 16], "little")
        rsize = int.from_bytes(data[section + 16:section + 20], "little")
        roff = int.from_bytes(data[section + 20:section + 24], "little")
        size = max(vsize, rsize)
        if vaddr <= rva < vaddr + size:
            off = roff + rva - vaddr
            return off if off < len(data) else None
    return None

def _read_c_string(data: bytes, offset: int) -> str | None:
    if not 0 <= offset < len(data): return None
    end = data.find(b"\0", offset)
    if end < 0: return None
    try: return data[offset:end].decode("ascii")
    except UnicodeDecodeError: return None

def _pe_imports(path: Path) -> list[str]:
    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ": return []
    pe = int.from_bytes(data[0x3C:0x40], "little")
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\0\0": return []
    optional = pe + 24
    if optional + 2 > len(data): return []
    magic = int.from_bytes(data[optional:optional + 2], "little")
    if magic not in (0x10B, 0x20B): return []
    directory = optional + (96 if magic == 0x10B else 112)
    import_entry = directory + 8
    if import_entry + 8 > len(data): return []
    import_rva = int.from_bytes(data[import_entry:import_entry + 4], "little")
    if not import_rva: return []
    descriptor = _rva_to_offset(data, import_rva)
    if descriptor is None: return []
    result = []
    for i in range(4096):
        base = descriptor + i * 20
        if base + 20 > len(data): break
        entry = data[base:base + 20]
        if entry == b"\0" * 20: break
        name_rva = int.from_bytes(entry[12:16], "little")
        name_offset = _rva_to_offset(data, name_rva)
        name = _read_c_string(data, name_offset) if name_offset is not None else None
        if name: result.append(name)
    return result

def _is_pe(path: Path) -> bool:
    try:
        with path.open("rb") as stream: return stream.read(2) == b"MZ"
    except OSError: return False

def _scan_host_paths(path: Path) -> list[str]:
    if path.suffix.lower() not in _TEXT_EXTENSIONS: return []
    try: data = path.read_bytes()
    except OSError as exc: raise PortableReleaseProofError(f"Unable to read release file: {path}") from exc
    return [m.group(0).decode("utf-8", errors="replace") for p in _HOST_PATH_PATTERNS if (m := p.search(data))]

def _packaged_files(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix().lower(): p for p in root.rglob("*") if p.is_file()}

def _packaged_dependency(source: Path, dependency: str, files: dict[str, Path], root: Path) -> bool:
    dependency_name = Path(dependency).name.lower()
    sibling = source.parent / dependency_name
    if sibling.is_file(): return True
    return sum(1 for path in files.values() if path.name.lower() == dependency_name) == 1

def _validate_zip_members(artifact: Path) -> int:
    try:
        with zipfile.ZipFile(artifact) as archive:
            names = [i.filename for i in archive.infolist()]
            if len(names) != len(set(names)): raise PortableReleaseProofError("Release artifact contains duplicate paths")
            for info in archive.infolist():
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000: raise PortableReleaseProofError(f"Release artifact contains a symlink: {info.filename}")
                normalized = info.filename.replace("\\", "/")
                if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized) or normalized == ".." or "../" in normalized:
                    raise PortableReleaseProofError(f"Release artifact contains an unsafe path: {info.filename}")
            return len(names)
    except zipfile.BadZipFile as exc: raise PortableReleaseProofError(f"Invalid release ZIP: {artifact}") from exc

def prove_portable_release(artifact: Path, *, manifest: Path | None = None) -> PortableReleaseProofReport:
    artifact = Path(artifact).resolve()
    if not artifact.is_file(): raise PortableReleaseProofError(f"Release artifact not found: {artifact}")
    try: release_manifest = release_package.validate_release_artifact(artifact, manifest)
    except release_package.ReleasePackageError as exc: raise PortableReleaseProofError(f"Release integrity validation failed: {exc}") from exc
    file_count = _validate_zip_members(artifact)
    application = release_manifest.get("application")
    version = release_manifest.get("application_version")
    if not isinstance(application, str) or not application: raise PortableReleaseProofError("Release manifest does not declare an application")
    if not isinstance(version, str) or not version: raise PortableReleaseProofError("Release manifest does not declare an application version")
    production = release_manifest.get("production_boundary") is True

    with tempfile.TemporaryDirectory(prefix="robostudio-rsd20p-") as temp:
        root = Path(temp) / "RelocatedRoboStudio"
        root.mkdir()
        with zipfile.ZipFile(artifact) as archive: archive.extractall(root)
        app = root / application
        if not app.is_file(): raise PortableReleaseProofError(f"Packaged application is missing: {application}")

        if production:
            try: production_artifact_boundary.validate_distribution_root(root)
            except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
                raise PortableReleaseProofError(f"Production artifact boundary validation failed: {exc}") from exc
            python = "target prerequisite: Python (not packaged)"
        else:
            python_name = "python.exe" if sys.platform == "win32" else "python"
            python_path = root / _RUNTIME_BIN / python_name
            if not python_path.is_file():
                raise PortableReleaseProofError(f"Portable Python runtime is missing: {(_RUNTIME_BIN / python_name).as_posix()}")
            for required in (_RUNTIME_PLATFORMIO / "platforms", _RUNTIME_PLATFORMIO / "packages", _RUNTIME_RESOURCES):
                if not (root / required).is_dir():
                    raise PortableReleaseProofError(f"Required packaged runtime directory is missing: {required.as_posix()}")
            python = str(python_path)

        files = _packaged_files(root)
        findings = []
        dependencies = set()
        system_count = packaged_count = 0
        for path in files.values():
            rel = path.relative_to(root).as_posix()
            for marker in _scan_host_paths(path): findings.append(DependencyFinding(rel, marker, "host-specific absolute path"))
            if not _is_pe(path): continue
            for dependency in _pe_imports(path):
                key = (rel, dependency.lower())
                if key in dependencies: continue
                dependencies.add(key)
                if _is_system_dependency(dependency): system_count += 1
                elif _packaged_dependency(path, dependency, files, root): packaged_count += 1
                else: findings.append(DependencyFinding(rel, dependency, "non-system PE dependency is not packaged"))
        return PortableReleaseProofReport(artifact, application, version, _sha256(artifact), file_count, python, len(dependencies), system_count, packaged_count, tuple(findings), not findings)

def report_to_dict(report: PortableReleaseProofReport) -> dict[str, object]:
    return {"schema": SCHEMA, "schema_version": SCHEMA_VERSION, "status": "PASS" if report.passed else "FAIL", "artifact": str(report.artifact), "application": report.application, "application_version": report.application_version, "artifact_sha256": report.artifact_sha256, "file_count": report.file_count, "runtime_python": report.runtime_python, "dependency_count": report.dependency_count, "system_dependency_count": report.system_dependency_count, "packaged_dependency_count": report.packaged_dependency_count, "findings": [{"source": item.source, "dependency": item.dependency, "reason": item.reason} for item in report.findings]}