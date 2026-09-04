#!/usr/bin/env python3
"""C3 API -> compiler -> VM -> MockHardware E2E coverage.

These tests intentionally stop at MockHardware. Physical ESP32 evidence is
tracked separately in the C3 matrix and cannot be claimed from this suite.
"""
import ast
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
FRONTEND_ROOT = ROOT / "robot-frontend-robosim"
sys.path.insert(0, str(COMPILER_ROOT))
sys.path.insert(0, str(FRONTEND_ROOT))

from frontend import rewrite
from compiler.compiler import RobotCompiler
from compiler.binary import ProgramEncoder
from compiler.generated.opcode import Opcode
from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, ISAOperand
from runtime import ProgramLoader, VirtualMachine
from runtime.hardware import MockHardware


def compile_robosim(source: str):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as src:
        src.write(source)
        src_path = Path(src.name)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rewrite.py", delete=False) as dst:
        rewrite_path = Path(dst.name)
    try:
        rewrite(src_path, rewrite_path)
        return RobotCompiler().compile(rewrite_path)
    finally:
        src_path.unlink(missing_ok=True)
        rewrite_path.unlink(missing_ok=True)


def convert_instruction(ins):
    opcode = Opcode(ins.opcode)
    operands = []
    if opcode == Opcode.LoadConst:
        operands = [ISAOperand.integer(ins.p1),
                    ISAOperand.float(ins.p2) if isinstance(ins.p2, float)
                    else ISAOperand.integer(ins.p2)]
    elif opcode in (Opcode.Forward, Opcode.Backward, Opcode.TurnLeft,
                    Opcode.TurnRight, Opcode.Wait):
        operands = [ISAOperand.integer(ins.p1)]
    elif opcode == Opcode.Stop:
        operands = []
    elif opcode in (Opcode.Jump,):
        operands = [ISAOperand.integer(ins.p2)]
    elif opcode in (Opcode.JumpIfFalse, Opcode.JumpIfTrue):
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode in (Opcode.Add, Opcode.Sub, Opcode.Mul, Opcode.Div,
                    Opcode.Mod, Opcode.Pow, Opcode.CompareEQ,
                    Opcode.CompareNE, Opcode.CompareLT, Opcode.CompareLE,
                    Opcode.CompareGT, Opcode.CompareGE):
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2),
                     ISAOperand.integer(ins.p3)]
    elif opcode == Opcode.Neg:
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p3)]
    elif opcode == Opcode.Store:
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode == Opcode.Call:
        operands = [ISAOperand.integer(ins.p1)]
    elif opcode == Opcode.Return:
        operands = []
    elif opcode in (Opcode.ReadUltrasonic, Opcode.ReadColor):
        operands = [ISAOperand.integer(ins.p1)]
    elif opcode in (Opcode.ReadTouch, Opcode.ReadLight, Opcode.ReadLine):
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode in (Opcode.GetTraceValue, Opcode.GetTraceState, Opcode.GetTraceRaw):
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2), ISAOperand.integer(ins.p3)]
    elif opcode in (Opcode.Set3CLed, Opcode.SetLightSensorLed):
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode == Opcode.SetMotorSpeed:
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    elif opcode in (Opcode.LineBasis, Opcode.LineFollow):
        operands = [ISAOperand.integer(ins.p1)]
    elif opcode == Opcode.LineMillisecond:
        operands = [ISAOperand.integer(ins.p1), ISAOperand.integer(ins.p2)]
    else:
        for value in (ins.p1, ins.p2, ins.p3):
            if value != 0:
                operands.append(ISAOperand.integer(value))
    return ISAInstruction(opcode, operands)


def run_source(source: str, hardware=None):
    program = compile_robosim(source)
    isa = ISAProgram()
    fn = ISAFunction("main")
    for ins in program.instructions:
        fn.add_instruction(convert_instruction(ins))
    isa.add_function(fn)

    binary = ProgramEncoder().encode(isa)
    runtime_program = ProgramLoader().load(binary)
    hardware = hardware or MockHardware()
    vm = VirtualMachine(hardware=hardware)
    vm.load(runtime_program)

    result = {"error": None}
    thread = threading.Thread(target=lambda: _run(vm, result))
    thread.start()
    thread.join(5)
    if thread.is_alive():
        vm.stop()
        thread.join(1)
        raise AssertionError("VM execution timed out")
    if result["error"]:
        raise result["error"]
    assert vm.state.value == "finished"
    return hardware, program


def _run(vm, result):
    try:
        vm.run()
    except Exception as exc:
        result["error"] = exc


def test_movement_and_wait():
    hw, _ = run_source("""
import rcu
rcu.SetMoveRun("forward", 80)
rcu.SetWaitForTime(1)
rcu.SetMoveStop()
""")
    motors = [x for x in hw.log if x[0] == "set_motor"]
    assert motors == [("set_motor", 80, 80), ("set_motor", 0, 0)]


def test_ultrasonic_decision_to_motor():
    hw = MockHardware()
    hw.set_ultrasonic_value(10)
    hw, _ = run_source("""
import rcu
dist = rcu.GetUltrasound(1)
if dist < 20:
    rcu.SetMoveStop()
else:
    rcu.SetMoveRun("forward", 80)
""", hw)
    assert ("read_ultrasonic",) in hw.log
    assert ("set_motor", 0, 0) in hw.log


def test_touch_and_light_reads():
    hw = MockHardware()
    hw.set_touch_value(1, True)
    hw.set_light_value(777)
    hw, _ = run_source("""
import rcu
touch = rcu.GetTouch(1)
light = rcu.GetLightSensor(1)
""", hw)
    assert ("read_touch", 1) in hw.log
    assert ("read_light", 1) in hw.log


def test_line_sensor_and_trace():
    hw = MockHardware()
    hw.set_line_value(0, 900)
    hw.set_line_value(1, 0)
    hw.set_line_value(2, 0)
    hw, program = run_source("""
import rcu
line = rcu.GetTraceV2I2CChxState(1, 0)
value = rcu.GetTraceV2I2C(1, 0)
raw = rcu.GetTraceV2I2CData(1)
""", hw)
    assert ("read_line_sensor", 0) in hw.log
    assert program.instructions


def test_led_output():
    hw, _ = run_source("""
import rcu
rcu.Set3CLed(1, 1)
rcu.Set3CLed(1, 0)
""")
    leds = [x for x in hw.log if x[0] == "set_led"]
    assert leds == [("set_led", 1, 1), ("set_led", 1, 0)]


def test_line_millisecond_execution():
    hw = MockHardware()
    hw.set_line_value(0, 900)
    hw.set_line_value(1, 900)
    hw.set_line_value(2, 900)
    hw, _ = run_source("""
import rcu
rcu.line_millisecond(50, 1)
""", hw)
    motors = [x for x in hw.log if x[0] == "set_motor"]
    assert motors
    assert motors[-1] == ("set_motor", 0, 0)


def test_api_compile_and_vm_matrix():
    # These are P0 APIs with an existing runtime/platform path.
    programs = [
        "import rcu\nrcu.SetMoveRun('forward', 20)\nrcu.SetMoveStop()\n",
        "import rcu\nrcu.Set3CLed(1, 1)\nrcu.Set3CLed(1, 0)\n",
        "import rcu\nx = rcu.GetUltrasound(1)\n",
        "import rcu\nx = rcu.GetTouch(1)\n",
        "import rcu\nx = rcu.GetLightSensor(1)\n",
        "import rcu\nx = rcu.GetTraceV2I2CData(1)\n",
        "import rcu\nrcu.line_basis(50)\nrcu.line_stop()\n",
    ]
    for source in programs:
        run_source(source)


if __name__ == "__main__":
    tests = [
        test_movement_and_wait,
        test_ultrasonic_decision_to_motor,
        test_touch_and_light_reads,
        test_line_sensor_and_trace,
        test_led_output,
        test_line_millisecond_execution,
        test_api_compile_and_vm_matrix,
    ]
    failed = []
    for test in tests:
        try:
            test()
            print(f"{test.__name__}: PASS")
        except Exception as exc:
            failed.append((test.__name__, str(exc)))
            print(f"{test.__name__}: FAIL - {exc}")
    raise SystemExit(1 if failed else 0)
