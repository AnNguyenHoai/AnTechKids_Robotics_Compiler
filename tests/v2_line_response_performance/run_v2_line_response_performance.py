from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/line_response_report.py"
API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
SERIAL = ROOT / "robot-platform/main/src/Communication/SerialCommandHandler.cpp"
DOC = ROOT / "robot-docs/motor-control/H23-D_LINE_RESPONSE_LATENCY_TRACE.md"

spec = importlib.util.spec_from_file_location("line_response_report", TOOL)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

SAMPLE_LOG = """noise
[LINE-RESPONSE] t=1000us mask=0x04 prev=--- loop=0us | sensor=120us control=30us output=15us total=165us | cmd L=50 R=50
[LINE-RESPONSE] t=2000us mask=0x0C prev=4 loop=1000us | sensor=140us control=40us output=20us total=200us | cmd L=35 R=65
[LINE-RESPONSE] t=3100us mask=0x18 prev=12 loop=1100us | sensor=180us control=35us output=25us total=240us | cmd L=20 R=80
"""


def test_parser_and_summary() -> None:
    samples = module.parse_lines(SAMPLE_LOG.splitlines())
    assert len(samples) == 3
    assert samples[0].mask == 0x04
    assert samples[1].sensor_us == 140
    assert samples[2].left_cmd == 20

    summary = module.summarize(samples)
    assert summary["sensor_us"]["count"] == 3
    assert summary["sensor_us"]["min"] == 120
    assert summary["sensor_us"]["max"] == 180
    assert summary["total_us"]["median"] == 200
    assert summary["output_us"]["mean"] == 20.0


def test_cli_never_invents_threshold_or_pass_fail() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        log = td / "line.log"
        csv_path = td / "samples.csv"
        log.write_text(SAMPLE_LOG, encoding="utf-8")
        raw = subprocess.check_output(
            [sys.executable, str(TOOL), str(log), "--label", "v2-mcp23017", "--csv", str(csv_path)],
            text=True,
        )
        report = json.loads(raw)
        assert report["label"] == "v2-mcp23017"
        assert report["sample_count"] == 3
        assert report["acceptance_threshold"] is None
        assert report["pass_fail"] == "NOT_EVALUATED"
        assert csv_path.exists()
        assert "sensor_us" in csv_path.read_text(encoding="utf-8")


def test_production_instrumentation_contract() -> None:
    api = API.read_text(encoding="utf-8")
    serial = SERIAL.read_text(encoding="utf-8")

    required = (
        "const uint32_t sensorStartUs = micros();",
        "const uint32_t sensorDoneUs = micros();",
        "const uint32_t controlDoneUs = micros();",
        "const uint32_t outputDoneUs = micros();",
        "(sensorDoneUs - sensorStartUs)",
        "(controlDoneUs - sensorDoneUs)",
        "(outputDoneUs - controlDoneUs)",
        "(outputDoneUs - sensorStartUs)",
        "[LINE-RESPONSE]",
    )
    for marker in required:
        assert marker in api, marker

    assert 'input == "line diag on"' in serial
    assert 'input == "line diag off"' in serial
    assert 'input == "line diag status"' in serial
    assert "setLineResponseDiagnosticEnabled(true)" in serial


def test_documentation_is_v2_line5_and_hardware_threshold_pending() -> None:
    doc = DOC.read_text(encoding="utf-8")
    assert "canonical 5-bit" in doc
    assert "V1 direct GPIO" in doc
    assert "V2 MCP23017" in doc
    assert "threshold" in doc.lower()
    assert "must not" in doc.lower() or "do not" in doc.lower()
    assert "3-channel" not in doc


def main() -> int:
    test_parser_and_summary()
    print("PASS: Line response parser extracts and summarizes latency fields")
    test_cli_never_invents_threshold_or_pass_fail()
    print("PASS: report tool records evidence without inventing acceptance threshold")
    test_production_instrumentation_contract()
    print("PASS: production diagnostic preserves sensor/control/output/total timestamps")
    test_documentation_is_v2_line5_and_hardware_threshold_pending()
    print("PASS: measurement protocol is V1-vs-V2 comparable and threshold remains hardware-owned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
