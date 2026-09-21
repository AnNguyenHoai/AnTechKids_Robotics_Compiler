#!/usr/bin/env python3
"""H33 Capability-Compiler Binding regression gate."""
from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
FRONTEND_ROOT = ROOT / "robot-frontend-robosim"
for path in (COMPILER_ROOT, FRONTEND_ROOT, ROOT):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from compiler.compiler import RobotCompiler
from compiler.error import CompilerError
from compiler.robostudio_bridge import CompileRequest, compile_request
import compiler.target_contract as target_contract_module
from frontend.rewriter import rewrite
from tools import production_distribution

PASS = 0


def check(condition: bool, label: str) -> None:
    global PASS
    if not condition:
        raise AssertionError(label)
    PASS += 1
    print(f"PASS: {label}")


def expect_code(code: str, action, label: str) -> CompilerError:
    try:
        action()
    except CompilerError as exc:
        check(exc.code == code, f"{label}: {code}")
        return exc
    raise AssertionError(f"{label}: expected {code}")


def compile_source(source: str, target: str):
    return RobotCompiler(target=target).compile_ast(ast.parse(source))


def test_target_and_capability_binding() -> None:
    expect_code(
        "E_TARGET_UNKNOWN",
        lambda: RobotCompiler(target="unknown-h33-target"),
        "unknown target fails before compilation",
    )

    compile_source("forward(50)\n", "esp32")
    check(True, "supported API compiles for esp32")

    exc = expect_code(
        "E_CAPABILITY_MISSING",
        lambda: compile_source('set_move_initialize(1, 2, "normal")\n', "esp32"),
        "encoder movement is rejected on esp32",
    )
    diagnostic = exc.to_diagnostic()
    check(diagnostic["context"]["capability"] == "motion.encoder_angle", "diagnostic identifies missing capability")
    check(diagnostic["context"]["target"] == "esp32", "diagnostic identifies target")

    compile_source('set_move_initialize(1, 2, "normal")\n', "robosim")
    check(True, "robosim keeps encoder movement capability")

    expect_code(
        "E_CAPABILITY_MISSING",
        lambda: compile_source("set_lizard(1)\n", "arduino"),
        "arduino rejects unsupported lizard peripheral",
    )
    compile_source("set_lizard(1)\n", "esp32")
    check(True, "esp32 accepts lizard peripheral")

    compiler = RobotCompiler(target="esp32")
    node = ast.parse("forward(1)\n").body[0].value
    expect_code(
        "E_API_UNSUPPORTED",
        lambda: compiler.target_contract.validate_api_call(
            "fake_api", {"opcode": "NotCanonical"}, node
        ),
        "unknown producer is rejected",
    )


def test_resource_contract() -> None:
    compile_source("value = read_line(2)\n", "esp32")
    check(True, "esp32 accepts canonical line channel 2")

    exc = expect_code(
        "E_RESOURCE_OUT_OF_RANGE",
        lambda: compile_source("value = read_line(3)\n", "esp32"),
        "esp32 rejects canonical line channel 3",
    )
    diagnostic = exc.to_diagnostic()
    check(diagnostic["context"]["resource"] == "sensor.line.channel", "resource diagnostic identifies line channel")
    check(diagnostic["context"]["resource_max"] == 2, "resource diagnostic carries target max")

    compile_source("value = read_line(6)\n", "robosim")
    check(True, "robosim accepts canonical line channel 6")

    expect_code(
        "E_DYNAMIC_RESOURCE_UNSAFE",
        lambda: compile_source("channel = 1\nvalue = read_line(channel)\n", "esp32"),
        "dynamic constrained resource fails closed",
    )


def test_robosim_adapter_to_target() -> None:
    with tempfile.TemporaryDirectory(prefix="h33-adapter-") as temp_name:
        temp = Path(temp_name)

        def rewrite_compile(channel: int, target: str):
            source = temp / f"trace_{channel}_{target}.py"
            rewritten = temp / f"trace_{channel}_{target}.rewrite.py"
            source.write_text(
                "import rcu\n"
                f"state = rcu.GetTraceV2I2CState(1, {channel})\n",
                encoding="utf-8",
            )
            rewrite(source, rewritten)
            text = rewritten.read_text(encoding="utf-8")
            program = RobotCompiler(target=target).compile(rewritten)
            return text, program

        text, _ = rewrite_compile(3, "esp32")
        check("get_trace_state(1, 2)" in text, "RoboSim channel 3 normalizes to canonical channel 2")

        expect_code(
            "E_RESOURCE_OUT_OF_RANGE",
            lambda: rewrite_compile(4, "esp32"),
            "RoboSim channel 4 reaches compiler and is rejected by esp32 target",
        )

        text, _ = rewrite_compile(7, "robosim")
        check("get_trace_state(1, 6)" in text, "RoboSim channel 7 is valid for robosim target")

        dynamic_source = temp / "trace_dynamic.py"
        dynamic_rewritten = temp / "trace_dynamic.rewrite.py"
        dynamic_source.write_text(
            "import rcu\nchannel = 2\nstate = rcu.GetTraceV2I2CState(1, channel)\n",
            encoding="utf-8",
        )
        rewrite(dynamic_source, dynamic_rewritten)
        dynamic_text = dynamic_rewritten.read_text(encoding="utf-8")
        check("channel - 1" in dynamic_text, "RoboSim dynamic channel is representation-normalized")
        expect_code(
            "E_DYNAMIC_RESOURCE_UNSAFE",
            lambda: RobotCompiler(target="esp32").compile(dynamic_rewritten),
            "dynamic RoboSim channel reaches compiler resource policy",
        )


def test_bridge_uses_same_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="h33-bridge-") as temp_name:
        temp = Path(temp_name)
        source = temp / "program.py"
        output = temp / "program.h"
        source.write_text("set_lizard(1)\n", encoding="utf-8")
        response = compile_request(
            CompileRequest(
                source=str(source),
                output=str(output),
                source_kind="standard-robot-python",
                target="arduino",
            )
        )
        check(response.status == "FAIL", "RoboStudio bridge rejects unsupported target API")
        check(response.error_code == "E_CAPABILITY_MISSING", "RoboStudio bridge preserves compiler error code")
        check(response.diagnostic is not None, "RoboStudio bridge returns structured diagnostic")
        check(not output.exists(), "failed target validation produces no output artifact")


def test_target_wiring_boundaries() -> None:
    check(RobotCompiler().target == "robosim", "generic compiler defaults to robosim")
    check(
        CompileRequest(source="input.py", output="program.h").target == "esp32",
        "RoboStudio bridge defaults to physical esp32 target",
    )

    build_text = (ROOT / "tools" / "build.py").read_text(encoding="utf-8")
    check(
        'default="esp32"' in build_text and '"--target",' in build_text,
        "standard physical build forwards explicit target",
    )

    physical_text = (ROOT / "tools" / "build_physical.py").read_text(encoding="utf-8")
    check(
        '"--target", "esp32"' in physical_text,
        "physical build chain binds esp32 explicitly",
    )


def test_invalid_profile_fails_closed() -> None:
    canonical = ROOT / "packages" / "robot-isa"
    original = target_contract_module._contract_directory
    with tempfile.TemporaryDirectory(prefix="h33-invalid-profile-") as temp_name:
        temp = Path(temp_name)
        shutil.copy2(canonical / "canonical_isa.json", temp / "canonical_isa.json")
        shutil.copy2(canonical / "capability_model.json", temp / "capability_model.json")
        (temp / "target_profiles.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "profiles": [
                        {
                            "id": "broken",
                            "description": "invalid",
                            "capabilities": ["does.not.exist"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        try:
            target_contract_module._contract_directory = lambda: temp
            expect_code(
                "E_TARGET_PROFILE_INVALID",
                lambda: target_contract_module.TargetContract("broken"),
                "malformed target profile fails closed",
            )
        finally:
            target_contract_module._contract_directory = original


def test_production_contract_packaging() -> None:
    compiler = ROOT / "robot-compiler"
    frontend = ROOT / "robot-frontend-robosim" / "frontend"
    canonical = ROOT / "packages" / "robot-isa"
    with tempfile.TemporaryDirectory(prefix="h33-prod-stage-") as temp_name:
        stage = Path(temp_name)
        staged_compiler, _ = production_distribution._stage_compiler(
            compiler, frontend, stage
        )
        contracts = staged_compiler / "contracts"
        for name in production_distribution.TARGET_CONTRACT_FILES:
            check((contracts / name).is_file(), f"production stages canonical contract {name}")
            check(
                (contracts / name).read_bytes() == (canonical / name).read_bytes(),
                f"staged {name} matches canonical source exactly",
            )


def test_h32_projection_not_consumed() -> None:
    source = (COMPILER_ROOT / "compiler" / "target_contract.py").read_text(encoding="utf-8")
    check("platform_contract.json" not in source, "compiler does not consume H32 generated projection")


def main() -> int:
    test_target_and_capability_binding()
    test_resource_contract()
    test_robosim_adapter_to_target()
    test_bridge_uses_same_contract()
    test_target_wiring_boundaries()
    test_invalid_profile_fails_closed()
    test_production_contract_packaging()
    test_h32_projection_not_consumed()
    print(f"H33 Capability-Compiler Binding: PASS ({PASS} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
