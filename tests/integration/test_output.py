"""
Output Integration Tests

Verifies LED and Buzzer operations.
"""

import sys
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "robot-compiler"))

from compiler.compiler import RobotCompiler
from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, ISAOperand
from compiler.generated.opcode import Opcode
from compiler.binary import ProgramEncoder
from runtime import ProgramLoader, VirtualMachine
from runtime.hardware import MockHardware

def compile_and_run(source_code: str):
    compiler = RobotCompiler()
    tree = ast.parse(source_code)
    program = compiler.compile_ast(tree)
    isa_prog = ISAProgram()
    func = ISAFunction("main")
    for ins in program.instructions:
        op = Opcode(ins.opcode)
        ops = []
        if op == Opcode.LoadConst:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.Set3CLed:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.SetMp3Play:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.SetLightSensorLed:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        func.add_instruction(ISAInstruction(op, ops))
    isa_prog.add_function(func)
    encoder = ProgramEncoder()
    binary_prog = encoder.encode(isa_prog)
    loader = ProgramLoader()
    runtime_prog = loader.load(binary_prog)
    hardware = MockHardware()
    vm = VirtualMachine(hardware=hardware)
    vm.load(runtime_prog)
    vm.run()
    return hardware.log

def run_test(verbose=False) -> dict:
    results = []
    passed = True

    # Since MockHardware doesn't log LED/buzzer, we just check no exception.
    # In real hardware, we could check GPIO state.
    def check_no_exception(desc, source):
        try:
            logs = compile_and_run(source)
            return True, "Executed without error"
        except Exception as e:
            return False, str(e)

    # Test 1: LED On
    source = "set_3c_led(1, 1)"
    ok, msg = check_no_exception("LED On", source)
    results.append(("LED On", ok, msg))
    if not ok: passed = False

    # Test 2: LED Off
    source = "set_3c_led(1, 0)"
    ok, msg = check_no_exception("LED Off", source)
    results.append(("LED Off", ok, msg))
    if not ok: passed = False

    # Test 3: Buzzer
    source = "set_mp3_play(1)"
    ok, msg = check_no_exception("Buzzer", source)
    results.append(("Buzzer", ok, msg))
    if not ok: passed = False

    # Test 4: Light Sensor LED
    source = "set_light_sensor_led(1, 1)"
    ok, msg = check_no_exception("Light Sensor LED", source)
    results.append(("Light Sensor LED", ok, msg))
    if not ok: passed = False

    return {
        "passed": passed,
        "message": f"{sum(1 for r in results if r[1])}/{len(results)} output tests passed",
        "metrics": {
            "tests": len(results),
            "passed": sum(1 for r in results if r[1]),
            "failed": sum(1 for r in results if not r[1]),
        },
        "logs": [f"{name}: {'PASS' if ok else 'FAIL'} {msg}" for name, ok, msg in results]
    }