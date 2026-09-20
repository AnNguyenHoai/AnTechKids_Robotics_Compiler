#!/usr/bin/env python3
"""Regression for user-visible generated artifact paths."""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for entry in (ROOT, ROOT / "robostudio"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from services.build_worker import BuildWorker
from tools import runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-artifact-output-") as temp:
        base = Path(temp)
        workspace = base / "compile temp"
        state = base / "User State With Spaces"
        workspace.mkdir()
        output = workspace / "program.h"
        report = workspace / "compile_report.json"
        rewritten = workspace / "rewrite.py"
        output.write_text("// program\n", encoding="utf-8")
        report.write_text("{}\n", encoding="utf-8")
        rewritten.write_text("print('ok')\n", encoding="utf-8")
        payload = {
            "schema": "antechkids.robostudio.compiler-contract",
            "contract_version": 1,
            "status": "PASS",
            "instruction_count": 7,
            "output": str(output),
            "report": str(report),
            "rewritten_source": str(rewritten),
        }
        original = runtime_paths.prepare_user_data_root
        try:
            runtime_paths.prepare_user_data_root = lambda *args, **kwargs: state
            published = BuildWorker._publish_contract_artifacts(payload)
        finally:
            runtime_paths.prepare_user_data_root = original

        for field in ("output", "report", "rewritten_source"):
            path = Path(published[field])
            check(f"{field} is published", path.is_file())
            check(f"{field} is durable user state", state in path.parents)
            check(f"{field} is outside disposable workspace", workspace not in path.parents)

        summary = BuildWorker._contract_summary(published, True)
        check("summary labels artifact section", "Output artifacts:" in summary)
        check("summary prints program header path", published["output"] in summary)
        check("summary prints compile report path", published["report"] in summary)
        check("summary prints rewritten source path", published["rewritten_source"] in summary)
        check("raw contract JSON is not required in UI", json.dumps(payload) not in summary)

    print("Artifact output contract checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
