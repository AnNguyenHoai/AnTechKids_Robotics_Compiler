"""Canonical production release CLI for RoboStudio."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
if __package__ in (None, ""):
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path: sys.path.insert(0, str(root))
from tools import portable_release_proof, production_release_assembly, release_acceptance, release_package

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.release_cli", description="Build and verify a production RoboStudio release.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="assemble and prove a production release")
    build.add_argument("--executable", required=True, type=Path)
    build.add_argument("--runtime-bin", required=False, type=Path, help=argparse.SUPPRESS)
    build.add_argument("--runtime-platformio", required=False, type=Path, help=argparse.SUPPRESS)
    build.add_argument("--runtime-resources", required=True, type=Path)
    build.add_argument("--version-file", type=Path, default=production_release_assembly.repository_root() / "VERSION")
    build.add_argument("--source-revision", type=str)
    build.add_argument("--output", type=Path, default=production_release_assembly.repository_root() / "releases" / "production")
    build.add_argument("--json", action="store_true", dest="as_json")
    verify = sub.add_parser("verify", help="verify a release ZIP and application dependency closure")
    verify.add_argument("artifact", type=Path); verify.add_argument("--manifest", type=Path); verify.add_argument("--json", action="store_true", dest="as_json")
    inspect = sub.add_parser("inspect", help="validate a release ZIP and print its manifest")
    inspect.add_argument("artifact", type=Path); inspect.add_argument("--manifest", type=Path); inspect.add_argument("--json", action="store_true", dest="as_json")
    accept = sub.add_parser("accept", help="run release acceptance")
    accept.add_argument("artifact", type=Path); accept.add_argument("--timeout", type=float, default=30.0); accept.add_argument("--report", type=Path); accept.add_argument("--json", action="store_true", dest="as_json")
    return parser

def _cmd_build(args: argparse.Namespace) -> int:
    try:
        revision = production_release_assembly._source_revision(args.source_revision)
        report = production_release_assembly.assemble_release(production_release_assembly.ProductionReleaseInputs(args.executable, args.runtime_resources, args.version_file, revision, args.runtime_bin, args.runtime_platformio), args.output)
    except production_release_assembly.ProductionReleaseAssemblyError as exc:
        print(f"RSD-20 build: FAIL: {exc}", file=sys.stderr); return 1
    if args.as_json: print(json.dumps(report, indent=2))
    else:
        print("RSD-20 release: PASS")
        print(f"Artifact: {report['artifact']}"); print(f"SHA-256: {report['artifact_sha256']}")
        print(f"Release manifest: {report['release_manifest']}"); print(f"Provenance: {report['release_provenance']}")
        print(f"Portable proof: {report['portable_proof_report']}"); print(f"Assembly report: {Path(args.output).resolve() / production_release_assembly.REPORT_NAME}")
    return 0

def _cmd_verify(args: argparse.Namespace) -> int:
    try: report = portable_release_proof.prove_portable_release(args.artifact, manifest=args.manifest)
    except portable_release_proof.PortableReleaseProofError as exc: print(f"RSD-20 verify: FAIL: {exc}", file=sys.stderr); return 1
    payload = portable_release_proof.report_to_dict(report)
    if args.as_json: print(json.dumps(payload, indent=2))
    else:
        print("RSD-20 verify: PASS" if report.passed else "RSD-20 verify: FAIL"); print(f"Artifact: {report.artifact}"); print(f"SHA-256: {report.artifact_sha256}"); print(f"Files: {report.file_count}"); print(f"Packaged dependencies: {report.packaged_dependency_count}")
        for finding in report.findings: print(f"Finding: {finding.reason}: {finding.dependency}")
    return 0 if report.passed else 1

def _cmd_inspect(args: argparse.Namespace) -> int:
    try: manifest = release_package.validate_release_artifact(args.artifact, args.manifest)
    except release_package.ReleasePackageError as exc: print(f"RSD-20 inspect: FAIL: {exc}", file=sys.stderr); return 1
    if args.as_json: print(json.dumps(manifest, indent=2))
    else:
        print("RSD-20 inspect: PASS"); print(f"Artifact: {args.artifact.resolve()}"); print(f"Application: {manifest.get('application')}"); print(f"Version: {manifest.get('application_version')}"); print(f"Files: {manifest.get('file_count')}"); print(f"Portable: {manifest.get('portable')}")
    return 0

def _cmd_accept(args: argparse.Namespace) -> int:
    try:
        report = release_acceptance.accept_release(args.artifact, timeout=args.timeout)
        evidence_path = release_acceptance.write_evidence(report, args.report) if args.report else None
    except (release_acceptance.ReleaseAcceptanceError, OSError) as exc: print(f"RSD-20 accept: FAIL: {exc}", file=sys.stderr); return 1
    payload = release_acceptance.report_to_dict(report)
    if evidence_path is not None: payload["evidence_report"] = str(evidence_path.resolve())
    if args.as_json: print(json.dumps(payload, indent=2))
    else:
        print("RSD-20 accept: PASS"); print(f"Artifact: {report.artifact}"); print(f"Application: {report.application}"); print(f"Version: {report.application_version}"); print(f"SHA-256: {report.artifact_sha256}"); print(f"Relocation verified: {payload['relocation_verified']}"); print(f"External CWD verified: {payload['external_cwd_verified']}"); print(f"Portable Python: {report.portable_python}"); print(f"Execution return code: {report.execution_returncode}"); print(f"Executable verified: {report.executable_verified}"); print(f"Environment verified: {report.environment_verified}")
        if evidence_path is not None: print(f"Acceptance evidence: {evidence_path.resolve()}")
    return 0

def main(argv: list[str] | None = None) -> int:
    parser = _build_parser(); args = parser.parse_args(argv)
    if args.command == "build": return _cmd_build(args)
    if args.command == "verify": return _cmd_verify(args)
    if args.command == "inspect": return _cmd_inspect(args)
    if args.command == "accept": return _cmd_accept(args)
    parser.error("unknown command"); return 2

if __name__ == "__main__": raise SystemExit(main())
