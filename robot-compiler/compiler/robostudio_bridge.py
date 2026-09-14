"""Stable RoboStudio -> RoboSim compiler application contract.

The GUI should depend on this narrow request/response boundary rather than on
compiler internals. The bridge accepts a RoboSim source file, rewrites it to
the Standard Robot API, invokes the real compiler, and emits machine-readable
result metadata.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path

from compiler.compiler import RobotCompiler
from compiler.emitter import HeaderEmitter
from frontend.rewriter import rewrite

CONTRACT_SCHEMA = "antechkids.robostudio.compiler-contract"
CONTRACT_VERSION = 1


@dataclass(frozen=True)
class CompileRequest:
    source: str
    output: str
    report: str | None = None
    source_kind: str = "robosim-python"


@dataclass(frozen=True)
class CompileResponse:
    schema: str
    contract_version: int
    status: str
    source_kind: str
    source: str
    rewritten_source: str | None
    output: str | None
    report: str | None
    instruction_count: int = 0
    error_code: str | None = None
    error_message: str | None = None


def _request(payload: dict) -> CompileRequest:
    if not isinstance(payload, dict):
        raise ValueError("request must be a JSON object")
    source = payload.get("source")
    output = payload.get("output")
    report = payload.get("report")
    source_kind = payload.get("source_kind", "robosim-python")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source must be a non-empty path")
    if not isinstance(output, str) or not output.strip():
        raise ValueError("output must be a non-empty path")
    if report is not None and not isinstance(report, str):
        raise ValueError("report must be a path or null")
    if source_kind not in {"robosim-python", "standard-robot-python"}:
        raise ValueError("source_kind must be 'robosim-python' or 'standard-robot-python'")
    return CompileRequest(source, output, report, source_kind)


def compile_request(request: CompileRequest) -> CompileResponse:
    source = Path(request.source).expanduser().resolve()
    output = Path(request.output).expanduser().resolve()
    report = Path(request.report).expanduser().resolve() if request.report else output.parent / "compile_report.json"
    if not source.is_file():
        return CompileResponse(CONTRACT_SCHEMA, CONTRACT_VERSION, "FAIL", request.source_kind, str(source), None, None, str(report), error_code="SOURCE_NOT_FOUND", error_message=f"Source file not found: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)

    rewritten: Path | None = None
    try:
        if request.source_kind == "robosim-python":
            fd, temp_name = tempfile.mkstemp(prefix="robostudio-rewrite-", suffix=".rewrite.py", dir=str(output.parent))
            Path(temp_name).unlink(missing_ok=True)
            rewritten = Path(temp_name)
            import os
            os.close(fd)
            rewrite(source, rewritten)
            compiler_source = rewritten
        else:
            compiler_source = source

        compiler = RobotCompiler()
        program = compiler.compile(compiler_source)
        HeaderEmitter().emit(program, output)
        report_payload = {
            "schema": CONTRACT_SCHEMA,
            "contract_version": CONTRACT_VERSION,
            "status": "PASS",
            "source_kind": request.source_kind,
            "input": str(source),
            "rewritten_source": str(rewritten) if rewritten else None,
            "output": str(output),
            "instruction_count": len(program.instructions),
            "variable_count": compiler.global_scope.next_index,
            "temp_count": compiler.temp_id,
            "function_count": len(compiler.functions),
        }
        report.write_text(json.dumps(report_payload, indent=2) + "\n", encoding="utf-8")
        return CompileResponse(CONTRACT_SCHEMA, CONTRACT_VERSION, "PASS", request.source_kind, str(source), str(rewritten) if rewritten else None, str(output), str(report), instruction_count=len(program.instructions))
    except SyntaxError as exc:
        return CompileResponse(CONTRACT_SCHEMA, CONTRACT_VERSION, "FAIL", request.source_kind, str(source), str(rewritten) if rewritten else None, None, str(report), error_code="INVALID_SOURCE", error_message=str(exc))
    except Exception as exc:
        return CompileResponse(CONTRACT_SCHEMA, CONTRACT_VERSION, "FAIL", request.source_kind, str(source), str(rewritten) if rewritten else None, None, str(report), error_code="COMPILE_FAILED", error_message=str(exc))
    finally:
        if rewritten is not None:
            rewritten.unlink(missing_ok=True)


def run_stdio() -> int:
    """Process exactly one JSON request from stdin and return a process status."""
    try:
        payload = json.loads(sys.stdin.read())
        response = compile_request(_request(payload))
    except (json.JSONDecodeError, ValueError) as exc:
        response = CompileResponse(CONTRACT_SCHEMA, CONTRACT_VERSION, "FAIL", "unknown", "", None, None, None, error_code="INVALID_REQUEST", error_message=str(exc))
    print(json.dumps(asdict(response), sort_keys=True), flush=True)
    return 0 if response.status == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="RoboStudio compiler contract endpoint")
    parser.add_argument("--request", type=Path, help="JSON request file; otherwise read one request from stdin")
    args = parser.parse_args()
    if args.request:
        try:
            payload = json.loads(args.request.read_text(encoding="utf-8"))
            response = compile_request(_request(payload))
            print(json.dumps(asdict(response), indent=2))
            return 0 if response.status == "PASS" else 1
        except Exception as exc:
            print(json.dumps(asdict(CompileResponse(CONTRACT_SCHEMA, CONTRACT_VERSION, "FAIL", "unknown", str(args.request), None, None, None, error_code="INVALID_REQUEST", error_message=str(exc)))))
            return 1
    return run_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
