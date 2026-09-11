"""Production portable-release proof and dependency-closure validation.

RSD-20-P closes the gap between a structurally valid release ZIP and evidence
that the shipped artifact is self-contained enough to be copied to another
Windows machine without relying on the developer's Python, PlatformIO, virtual
environment, working directory, or embedded host paths.

The gate is intentionally offline: it never installs packages, resolves
anything from PATH, or contacts a package index. PE imports are checked against
the files physically present in the artifact; Windows system DLL/API-set names
are treated as OS dependencies. Text and binary payloads are also scanned for
host-specific paths that commonly leak from build machines.
"""
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

# Direct CLI execution starts with ``tools`` on sys.path. Bootstrap the
# repository root before importing sibling modules; packaged/source imports
# remain unchanged.
if __package__ in (None, ""):
    _repository_root = Path(__file__).resolve().parent.parent
    if str(_repository_root) not in sys.path:
        sys.path.insert(0, str(_repository_root))

from tools import release_package

SCHEMA = "antechkids.robostudio.production-portable-release-proof"
SCHEMA_VERSION = 1

_RUNTIME_BIN = Path("runtime") / "bin"
_RUNTIME_PLATFORMIO = Path("runtime") / "platformio"
_RUNTIME_RESOURCES = Path("runtime") / "resources"

_SYSTEM_DLLS = {
    "advapi32.dll", "bcrypt.dll", "combase.dll", "comdlg32.dll", "crypt32.dll",
    "d3d9.dll", "dwmapi.dll", "gdi32.dll", "gdi32full.dll", "imm32.dll",
    "iphlpapi.dll", "kernel32.dll", "kernelbase.dll", "mpr.dll", "msimg32.dll",
    "msvcp_win.dll", "msvcrt.dll", "netapi32.dll", "ntdll.dll", "ole32.dll",
    "oleaut32.dll", "opengl32.dll", "powrprof.dll", "psapi.dll", "rpcrt4.dll",
    "secur32.dll", "shell32.dll", "shlwapi.dll", "user32.dll", "userenv.dll",
    "uxtheme.dll", "version.dll", "winhttp.dll", "wininet.dll", "winmm.dll",
    "winspool.drv", "ws2_32.dll", "wldap32.dll", "setupapi.dll", "cfgmgr32.dll",
    "comctl32.dll", "dxgi.dll", "d3d11.dll", "d3dcompiler_47.dll",
    "vcruntime140.dll", "vcruntime140_1.dll", "ucrtbase.dll",
}
_SYSTEM_DLL_PREFIXES = ("api-ms-win-", "ext-ms-win-")
_HOST_PATH_PATTERNS = (
    re.compile(rb"(?i)[a-z]:[\\/]+users[\\/]+"),
    re.compile(rb"(?i)[a-z]:[\\/]+program files[\\/]+(?:python|platformio)"),
    re.compile(rb"(?i)[a-z]:[\\/]+programdata[\\/]+platformio"),
    re.compile(rb"(?i)[a-z]:[\\/]+(?:\.platformio|pypoetry)"),
    re.compile(rb"(?i)[\\/]home[\\/]+"),
    re.compile(rb"(?i)[\\/]users[\\/]+"),
)


class PortableReleaseProofError(RuntimeError):
    """Raised when a release cannot prove portable dependency closure."""


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
    normalized = name.lower()
    return normalized in _SYSTEM_DLLS or normalized.startswith(_SYSTEM_DLL_PREFIXES)


def _rva_to_offset(data: bytes, rva: int) -> int | None:
    """Translate a PE RVA into a file offset without external PE libraries."""
    if len(data) < 0x40 or data[:2] != b"MZ":
        return None
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if pe_offset + 24 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        return None
    number_sections = int.from_bytes(data[pe_offset + 6:pe_offset + 8], "little")
    optional_size = int.from_bytes(data[pe_offset + 20:pe_offset + 22], "little")
    section_table = pe_offset + 24 + optional_size
    for index in range(number_sections):
        base = section_table + index * 40
        if base + 40 > len(data):
            return None
        virtual_size = int.from_bytes(data[base + 8:base + 12], "little")
        virtual_address = int.from_bytes(data[base + 12:base + 16], "little")
        raw_size = int.from_bytes(data[base + 16:base + 20], "little")
        raw_offset = int.from_bytes(data[base + 20:base + 24], "little")
        size = max(virtual_size, raw_size)
        if virtual_address <= rva < virtual_address + size:
            offset = raw_offset + (rva - virtual_address)
            return offset if offset < len(data) else None
    return None


def _read_c_string(data: bytes, offset: int) -> str | None:
    if offset < 0 or offset >= len(data):
        return None
    end = data.find(b"\0", offset)
    if end < 0:
        return None
    try:
        return data[offset:end].decode("ascii")
    except UnicodeDecodeError:
        return None


def _pe_imports(path: Path) -> list[str]:
    """Read normal PE import DLL names; return [] for non-PE files."""
    data = path.read_bytes()
    if len(data) < 0x40 or data[:2] != b"MZ":
        return []
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    if pe_offset + 24 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        return []
    optional_offset = pe_offset + 24
    if optional_offset + 2 > len(data):
        return []
    magic = int.from_bytes(data[optional_offset:optional_offset + 2], "little")
    if magic not in (0x10B, 0x20B):
        return []
    data_directory_offset = optional_offset + (96 if magic == 0x10B else 112)
    import_directory = data_directory_offset + 8
    if import_directory + 8 > len(data):
        return []
    import_rva = int.from_bytes(data[import_directory:import_directory + 4], "little")
    if import_rva == 0:
        return []
    descriptor_offset = _rva_to_offset(data, import_rva)
    if descriptor_offset is None:
        return []
    result: list[str] = []
    for index in range(4096):
        base = descriptor_offset + index * 20
        if base + 20 > len(data):
            break
        descriptor = data[base:base + 20]
        if descriptor == b"\0" * 20:
            break
        name_rva = int.from_bytes(descriptor[12:16], "little")
        name_offset = _rva_to_offset(data, name_rva)
        if name_offset is None:
            continue
        name = _read_c_string(data, name_offset)
        if name:
            result.append(name)
    return result


def _is_pe(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(2) == b"MZ"
    except OSError:
        return False


def _scan_host_paths(path: Path) -> list[str]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PortableReleaseProofError(f"Unable to read release file: {path}") from exc
    findings: list[str] = []
    for pattern in _HOST_PATH_PATTERNS:
        match = pattern.search(data)
        if match:
            findings.append(match.group(0).decode("utf-8", errors="replace"))
    return findings


def _packaged_files(root: Path) -> dict[str, Path]:
    return {path.relative_to(root).as_posix().lower(): path for path in root.rglob("*") if path.is_file()}


def _validate_zip_members(artifact: Path) -> int:
    try:
        with zipfile.ZipFile(artifact, "r") as archive:
            names = [info.filename for info in archive.infolist()]
            if len(names) != len(set(names)):
                raise PortableReleaseProofError("Release artifact contains duplicate paths")
            for info in archive.infolist():
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise PortableReleaseProofError(f"Release artifact contains a symlink: {info.filename}")
                normalized = info.filename.replace("\\", "/")
                if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized) or "../" in normalized or normalized == "..":
                    raise PortableReleaseProofError(f"Release artifact contains an unsafe path: {info.filename}")
            return len(names)
    except zipfile.BadZipFile as exc:
        raise PortableReleaseProofError(f"Invalid release ZIP: {artifact}") from exc


def prove_portable_release(artifact: Path, *, manifest: Path | None = None) -> PortableReleaseProofReport:
    """Validate release integrity and prove offline dependency closure."""
    artifact = Path(artifact).resolve()
    if not artifact.is_file():
        raise PortableReleaseProofError(f"Release artifact not found: {artifact}")
    try:
        release_manifest = release_package.validate_release_artifact(artifact, manifest)
    except release_package.ReleasePackageError as exc:
        raise PortableReleaseProofError(f"Release integrity validation failed: {exc}") from exc

    file_count = _validate_zip_members(artifact)
    application = release_manifest.get("application")
    version = release_manifest.get("application_version")
    if not isinstance(application, str) or not application:
        raise PortableReleaseProofError("Release manifest does not declare an application")
    if not isinstance(version, str) or not version:
        raise PortableReleaseProofError("Release manifest does not declare an application version")

    with tempfile.TemporaryDirectory(prefix="robostudio-rsd20p-") as temp:
        root = Path(temp) / "RelocatedRoboStudio"
        root.mkdir()
        try:
            with zipfile.ZipFile(artifact, "r") as archive:
                archive.extractall(root)
        except (OSError, zipfile.BadZipFile) as exc:
            raise PortableReleaseProofError(f"Unable to extract release artifact: {exc}") from exc

        application_path = root / application
        if not application_path.is_file():
            raise PortableReleaseProofError(f"Packaged application is missing: {application}")
        python_name = "python.exe" if sys.platform == "win32" else "python"
        python_path = root / _RUNTIME_BIN / python_name
        if not python_path.is_file():
            raise PortableReleaseProofError(f"Portable Python runtime is missing: {(_RUNTIME_BIN / python_name).as_posix()}")
        for required in (_RUNTIME_PLATFORMIO / "platforms", _RUNTIME_PLATFORMIO / "packages", _RUNTIME_RESOURCES):
            if not (root / required).is_dir():
                raise PortableReleaseProofError(f"Required packaged runtime directory is missing: {required.as_posix()}")

        files = _packaged_files(root)
        findings: list[DependencyFinding] = []
        packaged_count = 0
        system_count = 0
        dependency_names: set[tuple[str, str]] = set()

        for path in files.values():
            for marker in _scan_host_paths(path):
                findings.append(DependencyFinding(path.relative_to(root).as_posix(), marker, "host-specific absolute path"))
            if not _is_pe(path):
                continue
            for dependency in _pe_imports(path):
                key = (path.relative_to(root).as_posix(), dependency.lower())
                if key in dependency_names:
                    continue
                dependency_names.add(key)
                if _is_system_dependency(dependency):
                    system_count += 1
                    continue
                if dependency.lower() in files:
                    packaged_count += 1
                else:
                    findings.append(DependencyFinding(path.relative_to(root).as_posix(), dependency, "non-system PE dependency is not packaged"))

        return PortableReleaseProofReport(
            artifact=artifact,
            application=application,
            application_version=version,
            artifact_sha256=_sha256(artifact),
            file_count=file_count,
            runtime_python=str(python_path),
            dependency_count=len(dependency_names),
            system_dependency_count=system_count,
            packaged_dependency_count=packaged_count,
            findings=tuple(findings),
            passed=not findings,
        )


def report_to_dict(report: PortableReleaseProofReport) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if report.passed else "FAIL",
        "artifact": str(report.artifact),
        "application": report.application,
        "application_version": report.application_version,
        "artifact_sha256": report.artifact_sha256,
        "file_count": report.file_count,
        "runtime_python": report.runtime_python,
        "dependency_count": report.dependency_count,
        "system_dependency_count": report.system_dependency_count,
        "packaged_dependency_count": report.packaged_dependency_count,
        "findings": [
            {"source": finding.source, "dependency": finding.dependency, "reason": finding.reason}
            for finding in report.findings
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prove a RoboStudio release is portable and dependency-closed")
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    try:
        report = prove_portable_release(args.artifact, manifest=args.manifest)
    except PortableReleaseProofError as exc:
        print(f"RSD-20-P production portable release proof: FAIL: {exc}")
        return 1

    payload = report_to_dict(report)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not report.passed:
        print("RSD-20-P production portable release proof: FAIL")
        print(json.dumps(payload, indent=2))
        return 1
    print("RSD-20-P production portable release proof: PASS")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
