"""RSD-21.5 production artifact E2E contract regression suite."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tools import production_e2e


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-21-5-test-") as td:
        root = Path(td)
        artifact = root / "production.zip"
        source = root / "sample.py"
        source.write_text("print('robosim e2e')\n", encoding="utf-8")
        result = production_e2e.evaluate_production_artifact(
            artifact=artifact, source=source, launch=False
        )
        payload = result.to_dict()
        check("E2E report is machine-readable", json.loads(json.dumps(payload)) == payload)
        check("E2E report has PASS/FAIL status", payload["status"] in {"PASS", "FAIL"})
        check("E2E identifies production artifact", payload["artifact"] == str(artifact))
        check("target prerequisites remain external", payload["target_machine_prerequisites"] is True)
        check("source-tree execution is forbidden", payload["source_tree_execution"] is False)
    print("PASS: RSD-21.5 contract regression suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
