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
        elif op == Opcode.ReadUltrasonic:
            ops.append(ISAOperand.integer(ins.p1))  # dest
        elif op == Opcode.Store:
            ops.append(ISAOperand.integer(ins.p1))  # src
            ops.append(ISAOperand.integer(ins.p2))  # dest
        elif op in (Opcode.CompareEQ, Opcode.CompareNE, Opcode.CompareLT,
                    Opcode.CompareLE, Opcode.CompareGT, Opcode.CompareGE):
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
            ops.append(ISAOperand.integer(ins.p3))
        elif op == Opcode.JumpIfFalse:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.JumpIfTrue:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.Jump:
            ops.append(ISAOperand.integer(ins.p2))
        elif op in (Opcode.Forward, Opcode.Backward, Opcode.TurnLeft, Opcode.TurnRight):
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Stop:
            pass
        elif op == Opcode.SetMotorSpeed:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        else:
            # fallback for any other opcode
            if ins.p1 != 0:
                ops.append(ISAOperand.integer(ins.p1))
            if ins.p2 != 0:
                ops.append(ISAOperand.integer(ins.p2))
            if ins.p3 != 0:
                ops.append(ISAOperand.integer(ins.p3))
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

    # Test 1: Simple forward
    source = "forward(80)\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(80, 80), (0, 0)])
        results.append(("Forward", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Forward", False, str(e)))
        passed = False

    # Test 2: Variable and turn
    source = "speed = 50\nturn_left(speed)\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(-50, 50), (0, 0)])
        results.append(("Variable Turn", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Variable Turn", False, str(e)))
        passed = False

    # Test 3: Sensor condition
    source = """
dist = read_ultrasonic()
if dist < 20:
    turn_left(50)
else:
    forward(50)
stop()
"""
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(50, 50), (0, 0)])
        results.append(("Sensor Condition", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Sensor Condition", False, str(e)))
        passed = False

    # Test 4: SetMotorSpeed
    source = "set_motor_speed(40, 70)\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(40, 70), (0, 0)])
        results.append(("SetMotorSpeed", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("SetMotorSpeed", False, str(e)))
        passed = False

    # Test 5: While loop
    source = "speed = 80\nwhile speed > 50:\n    forward(80)\n    speed = 30\nstop()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_motor(logs, [(80, 80), (0, 0)])
        results.append(("While Loop", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("While Loop", False, str(e)))
        passed = False

    return {
        "passed": passed,
        "message": f"{sum(1 for r in results if r[1])}/{len(results)} compile-execute tests passed",
        "metrics": {
            "tests": len(results),
            "passed": sum(1 for r in results if r[1]),
            "failed": sum(1 for r in results if not r[1]),
        },
        "logs": [f"{name}: {'PASS' if ok else 'FAIL'} {msg}" for name, ok, msg in results]
    }