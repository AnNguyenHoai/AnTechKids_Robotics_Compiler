"""
Control Flow Integration Tests

Verifies if, while, nested loops, jumps, compare, return, etc.
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
        elif op in (Opcode.CompareEQ, Opcode.CompareNE, Opcode.CompareLT,
                    Opcode.CompareLE, Opcode.CompareGT, Opcode.CompareGE):
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
            ops.append(ISAOperand.integer(ins.p3))
        elif op in (Opcode.JumpIfFalse, Opcode.JumpIfTrue):
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.Jump:
            ops.append(ISAOperand.integer(ins.p2))
        elif op in (Opcode.Forward, Opcode.Backward, Opcode.TurnLeft, Opcode.TurnRight):
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Stop:
            pass
        elif op == Opcode.Store:
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

    def check_motor(logs, expected_calls):
        motor_calls = [item for item in logs if item[0] == "set_motor"]
        if len(motor_calls) != len(expected_calls):
            return False, f"Expected {len(expected_calls)} motor calls, got {len(motor_calls)}"
        for i, (exp_left, exp_right) in enumerate(expected_calls):
            if len(motor_calls[i]) < 3:
                return False, f"Motor call {i} has insufficient data: {motor_calls[i]}"
            if motor_calls[i][1] != exp_left or motor_calls[i][2] != exp_right:
                return False, f"Call {i}: expected ({exp_left},{exp_right}), got ({motor_calls[i][1]},{motor_calls[i][2]})"
        return True, ""

    # Test 1: If
    source = "speed = 80\nif speed > 50:\n    forward(80)\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(80, 80), (0, 0)])
        results.append(("If", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("If", False, str(e)))
        passed = False

    # Test 2: If-Else
    source = "speed = 30\nif speed > 50:\n    forward(80)\nelse:\n    backward(30)\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(-30, -30), (0, 0)])
        results.append(("If-Else", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("If-Else", False, str(e)))
        passed = False

    # Test 3: While
    source = "speed = 80\nwhile speed > 50:\n    forward(80)\n    speed = 30\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(80, 80), (0, 0)])
        results.append(("While", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("While", False, str(e)))
        passed = False

    # Test 4: Nested If
    source = "speed = 80\nturn = 40\nif speed > 50:\n    if turn < 60:\n        forward(80)\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(80, 80), (0, 0)])
        results.append(("Nested If", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Nested If", False, str(e)))
        passed = False

    # Test 5: Break
    source = "speed = 80\nwhile speed > 50:\n    forward(80)\n    break\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(80, 80), (0, 0)])
        results.append(("Break", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Break", False, str(e)))
        passed = False

    # Test 6: Continue (skip forward)
    source = "speed = 80\nwhile speed > 50:\n    speed = 30\n    continue\n    forward(80)\nstop()"
    try:
        logs = compile_and_run(source)
        # Only stop should be called
        ok, msg = check_motor(logs, [(0, 0)])
        results.append(("Continue", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Continue", False, str(e)))
        passed = False

    return {
        "passed": passed,
        "message": f"{sum(1 for r in results if r[1])}/{len(results)} control tests passed",
        "metrics": {
            "tests": len(results),
            "passed": sum(1 for r in results if r[1]),
            "failed": sum(1 for r in results if not r[1]),
        },
        "logs": [f"{name}: {'PASS' if ok else 'FAIL'} {msg}" for name, ok, msg in results]
    }