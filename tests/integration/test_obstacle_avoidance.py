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

def compile_and_run(source_code: str, hardware_setup=None):
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
        elif op == Opcode.CompareLT:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
            ops.append(ISAOperand.integer(ins.p3))
        elif op == Opcode.JumpIfFalse:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.Forward:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Backward:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.TurnLeft:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.TurnRight:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Stop:
            pass
        else:
            # fallback: add operands if present
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
    if hardware_setup:
        hardware_setup(hardware)
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

    # Scenario: Obstacle near (distance 15) -> turn left
    source = """
dist = read_ultrasonic()
if dist < 20:
    turn_left(50)
else:
    forward(50)
stop()
"""
    def setup_obstacle(hw):
        hw.set_ultrasonic_value(15)
    try:
        logs = compile_and_run(source, setup_obstacle)
        ok, msg = check_motor(logs, [(-50, 50), (0, 0)])
        results.append(("Obstacle Near -> Turn Left", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Obstacle Near -> Turn Left", False, str(e)))
        passed = False

    # Scenario: No obstacle (distance 50) -> forward
    source = """
dist = read_ultrasonic()
if dist < 20:
    turn_left(50)
else:
    forward(50)
stop()
"""
    def setup_no_obstacle(hw):
        hw.set_ultrasonic_value(50)
    try:
        logs = compile_and_run(source, setup_no_obstacle)
        ok, msg = check_motor(logs, [(50, 50), (0, 0)])
        results.append(("No Obstacle -> Forward", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("No Obstacle -> Forward", False, str(e)))
        passed = False

    # Scenario: Edge case - distance exactly threshold (20) -> forward
    source = """
dist = read_ultrasonic()
if dist < 20:
    turn_left(50)
else:
    forward(50)
stop()
"""
    def setup_edge(hw):
        hw.set_ultrasonic_value(20)
    try:
        logs = compile_and_run(source, setup_edge)
        ok, msg = check_motor(logs, [(50, 50), (0, 0)])
        results.append(("Edge Case 20", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Edge Case 20", False, str(e)))
        passed = False

    return {
        "passed": passed,
        "message": f"{sum(1 for r in results if r[1])}/{len(results)} obstacle avoidance tests passed",
        "metrics": {
            "tests": len(results),
            "passed": sum(1 for r in results if r[1]),
            "failed": sum(1 for r in results if not r[1]),
        },
        "logs": [f"{name}: {'PASS' if ok else 'FAIL'} {msg}" for name, ok, msg in results]
    }