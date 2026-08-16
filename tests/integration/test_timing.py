import sys
import ast
import time
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
        elif op == Opcode.Wait:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Forward:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Backward:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Stop:
            # no operands
            pass
        elif op == Opcode.TurnLeft:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.TurnRight:
            ops.append(ISAOperand.integer(ins.p1))
        else:
            # Nếu có opcode khác, ta vẫn thêm nhưng với operands rỗng (có thể gây lỗi)
            # Để an toàn, ta thêm nếu có p1, p2, p3
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
    start = time.time()
    vm.run()
    elapsed = time.time() - start
    return hardware.log, elapsed

def run_test(verbose=False) -> dict:
    results = []
    passed = True

    # Test 1: Wait 100ms
    source = "wait(100)"
    try:
        logs, elapsed = compile_and_run(source)
        ok = 0.08 <= elapsed <= 0.12
        results.append(("Wait 100ms", ok, f"{elapsed:.3f}s"))
        if not ok: passed = False
    except Exception as e:
        results.append(("Wait 100ms", False, str(e)))
        passed = False

    # Test 2: Wait 500ms
    source = "wait(500)"
    try:
        logs, elapsed = compile_and_run(source)
        ok = 0.45 <= elapsed <= 0.55
        results.append(("Wait 500ms", ok, f"{elapsed:.3f}s"))
        if not ok: passed = False
    except Exception as e:
        results.append(("Wait 500ms", False, str(e)))
        passed = False

    # Test 3: Wait 1000ms
    source = "wait(1000)"
    try:
        logs, elapsed = compile_and_run(source)
        ok = 0.95 <= elapsed <= 1.05
        results.append(("Wait 1000ms", ok, f"{elapsed:.3f}s"))
        if not ok: passed = False
    except Exception as e:
        results.append(("Wait 1000ms", False, str(e)))
        passed = False

    # Test 4: Repeated waits (3x200ms)
    source = "wait(200)\nwait(200)\nwait(200)"
    try:
        logs, elapsed = compile_and_run(source)
        ok = 0.55 <= elapsed <= 0.65
        results.append(("Repeated Waits", ok, f"{elapsed:.3f}s"))
        if not ok: passed = False
    except Exception as e:
        results.append(("Repeated Waits", False, str(e)))
        passed = False

    # Test 5: Wait with motion
    source = "forward(50)\nwait(300)\nbackward(30)"
    try:
        logs, elapsed = compile_and_run(source)
        motor_calls = [item for item in logs if item[0] == "set_motor"]
        # Expect forward(50,50) and backward(-30,-30)
        if len(motor_calls) >= 2:
            ok = 0.28 <= elapsed <= 0.32
            results.append(("Wait with Motion", ok, f"{elapsed:.3f}s"))
        else:
            results.append(("Wait with Motion", False, "Not enough motor calls"))
            passed = False
    except Exception as e:
        results.append(("Wait with Motion", False, str(e)))
        passed = False

    return {
        "passed": passed,
        "message": f"{sum(1 for r in results if r[1])}/{len(results)} timing tests passed",
        "metrics": {
            "tests": len(results),
            "passed": sum(1 for r in results if r[1]),
            "failed": sum(1 for r in results if not r[1]),
        },
        "logs": [f"{name}: {'PASS' if ok else 'FAIL'} {msg}" for name, ok, msg in results]
    }