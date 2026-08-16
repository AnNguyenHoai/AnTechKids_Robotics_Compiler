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
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.ReadTouch:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.ReadLight:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.ReadLine:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        elif op == Opcode.ReadColor:
            ops.append(ISAOperand.integer(ins.p1))
        elif op == Opcode.Store:
            ops.append(ISAOperand.integer(ins.p1))
            ops.append(ISAOperand.integer(ins.p2))
        else:
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

    def check_sensor_read(logs, sensor_type, expected_value=None):
        reads = [item for item in logs if item[0] == sensor_type]
        if not reads:
            return False, f"No {sensor_type} read detected"
        return True, ""

    # Test 1: Ultrasonic
    source = "dist = read_ultrasonic()"
    def setup_ultrasonic(hw):
        hw.set_ultrasonic_value(25)
    try:
        logs = compile_and_run(source, setup_ultrasonic)
        ok, msg = check_sensor_read(logs, "read_ultrasonic")
        results.append(("Ultrasonic", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Ultrasonic", False, str(e)))
        passed = False

    # Test 2: Touch
    source = "touch = read_touch(1)"
    def setup_touch(hw):
        hw.set_touch_value(1, True)
    try:
        logs = compile_and_run(source, setup_touch)
        ok, msg = check_sensor_read(logs, "read_touch")
        results.append(("Touch", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Touch", False, str(e)))
        passed = False

    # Test 3: Light
    source = "light = read_light(0)"
    def setup_light(hw):
        hw.set_light_value(512)
    try:
        logs = compile_and_run(source, setup_light)
        # Use 'read_light' instead of 'read_line_sensor'
        ok, msg = check_sensor_read(logs, "read_light")
        results.append(("Light", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Light", False, str(e)))
        passed = False

    # Test 4: Line
    source = "line = read_line(1)"
    def setup_line(hw):
        hw.set_line_value(1, 0)
    try:
        logs = compile_and_run(source, setup_line)
        ok, msg = check_sensor_read(logs, "read_line_sensor")
        results.append(("Line", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Line", False, str(e)))
        passed = False

    # Test 5: Color
    source = "color = read_color()"
    try:
        logs = compile_and_run(source)
        ok, msg = check_sensor_read(logs, "read_color")
        results.append(("Color", ok, msg))
        if not ok: passed = False
    except Exception as e:
        results.append(("Color", False, str(e)))
        passed = False

    return {
        "passed": passed,
        "message": f"{sum(1 for r in results if r[1])}/{len(results)} sensor tests passed",
        "metrics": {
            "tests": len(results),
            "passed": sum(1 for r in results if r[1]),
            "failed": sum(1 for r in results if not r[1]),
        },
        "logs": [f"{name}: {'PASS' if ok else 'FAIL'} {msg}" for name, ok, msg in results]
    }