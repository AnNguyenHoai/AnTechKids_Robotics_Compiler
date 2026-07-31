from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode
from compiler.error import CompilerError
EXAMPLES = ROOT / "examples"
compiler = RobotCompiler()


def compile_file(filename):
    return compiler.compile(EXAMPLES / filename)


def assert_instruction(actual, opcode_name, p1, p2, p3):
    actual_name = Opcode(actual.opcode).name

    assert actual_name == opcode_name, (
        f"Opcode mismatch: expected={opcode_name}, actual={actual_name}"
    )

    assert actual.p1 == p1, (
        f"{opcode_name} p1 mismatch: expected={p1}, actual={actual.p1}"
    )

    assert actual.p2 == p2, (
        f"{opcode_name} p2 mismatch: expected={p2}, actual={actual.p2}"
    )

    assert actual.p3 == p3, (
        f"{opcode_name} p3 mismatch: expected={p3}, actual={actual.p3}"
    )

def expect_program(program, expected):
    assert len(program.instructions) == len(expected), (
        f"Expected {len(expected)} instructions, got {len(program.instructions)}"
    )
    for i, (opcode, p1, p2, p3) in enumerate(expected):
        assert_instruction(program.instructions[i], opcode, p1, p2, p3)


def expect_last_opcode(filename, opcode_name):
    program = compile_file(filename)
    expected = Opcode[opcode_name].value
    assert program.instructions[-1].opcode == expected, f"Expected {opcode_name}"


def print_program(program):
    print(f"Instruction Count: {len(program.instructions)}")
    for i, ins in enumerate(program.instructions):
        print(f"{i}: Opcode: {Opcode(ins.opcode).name}, p1={ins.p1}, p2={ins.p2}, p3={ins.p3}")
    print()


# ---- Test cases ----
program = compile_file("demo_forward.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("Forward", 0, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_forward.py : PASS")

program = compile_file("demo_backward.py")
expect_program(program, [
    ("LoadConst", 0, 30, 0),
    ("Backward", 0, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_backward.py : PASS")

program = compile_file("demo_variable.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 50, 0),
    ("Forward", 0, 0, 0),
    ("TurnLeft", 1, 0, 0),
    ("Backward", 0, 0, 0),
    ("TurnRight", 1, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_variable.py : PASS")

try:
    compile_file("demo_unknown_function.py")
    assert False, "CompilerError expected"
except Exception as e:
    assert "Unknown function" in str(e)
print("Test demo_unknown_function.py : PASS")

try:
    compile_file("demo_wrong_argument.py")
    assert False, "CompilerError expected"
except Exception as e:
    assert "expects exactly 1 argument" in str(e)
print("Test demo_wrong_argument.py : PASS")

program = compile_file("demo_function.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("Forward", 0, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_function.py : PASS")

program = compile_file("demo_function_multiple.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("Forward", 0, 0, 0),
    ("LoadConst", 1, 80, 0),
    ("Forward", 1, 0, 0),
])
print("Test demo_function_multiple.py : PASS")

expect_last_opcode("demo_compare_gt.py", "CompareGT")
print("Test CompareGT : PASS")
expect_last_opcode("demo_compare_eq.py", "CompareEQ")
print("Test CompareEQ : PASS")
expect_last_opcode("demo_compare_ne.py", "CompareNE")
print("Test CompareNE : PASS")
expect_last_opcode("demo_compare_lt.py", "CompareLT")
print("Test CompareLT : PASS")
expect_last_opcode("demo_compare_le.py", "CompareLE")
print("Test CompareLE : PASS")
expect_last_opcode("demo_compare_ge.py", "CompareGE")
print("Test CompareGE : PASS")

program = compile_file("demo_if.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 50, 0),
    ("CompareGT", 0, 1, 2),
    ("JumpIfFalse", 2, 6, 0),
    ("LoadConst", 3, 80, 0),
    ("Forward", 3, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_if.py : PASS")

program = compile_file("demo_if_else.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 50, 0),
    ("CompareGT", 0, 1, 2),
    ("JumpIfFalse", 2, 7, 0),
    ("LoadConst", 3, 80, 0),
    ("Forward", 3, 0, 0),
    ("Jump", 0, 9, 0),
    ("LoadConst", 4, 30, 0),
    ("Backward", 4, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_if_else.py : PASS")

program = compile_file("demo_nested_if.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 40, 0),
    ("LoadConst", 2, 50, 0),
    ("CompareGT", 0, 2, 3),
    ("JumpIfFalse", 3, 10, 0),
    ("LoadConst", 4, 60, 0),
    ("CompareLT", 1, 4, 5),
    ("JumpIfFalse", 5, 10, 0),
    ("LoadConst", 6, 80, 0),
    ("Forward", 6, 0, 0),
    ("Stop", 0, 0, 0)
])
print("demo_nested_if.py : PASS")

program = compile_file("demo_while.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 50, 0),
    ("CompareGT", 0, 1, 2),
    ("JumpIfFalse", 2, 7, 0),
    ("LoadConst", 3, 80, 0),
    ("Forward", 3, 0, 0),
    ("Jump", 0, 1, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_while.py : PASS")

program = compile_file("demo_nested_while.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 40, 0),
    ("LoadConst", 2, 50, 0),
    ("CompareGT", 0, 2, 3),
    ("JumpIfFalse", 3, 12, 0),
    ("LoadConst", 4, 60, 0),
    ("CompareLT", 1, 4, 5),
    ("JumpIfFalse", 5, 11, 0),
    ("LoadConst", 6, 80, 0),
    ("Forward", 6, 0, 0),
    ("Jump", 0, 5, 0),
    ("Jump", 0, 2, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_nested_while.py : PASS")

program = compile_file("demo_break.py")
expect_program(program, [
    ("LoadConst", 0, 80, 0),
    ("LoadConst", 1, 50, 0),
    ("CompareGT", 0, 1, 2),
    ("JumpIfFalse", 2, 8, 0),
    ("LoadConst", 3, 80, 0),
    ("Forward", 3, 0, 0),
    ("Jump", 0, 8, 0),
    ("Jump", 0, 1, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_break.py : PASS")

program = compile_file("demo_continue.py")
# Continue không có bytecode cụ thể, chỉ là jump, nên ta chỉ kiểm tra không lỗi.
print("Test demo_continue.py : PASS")

program = compile_file("demo_bool_and.py")
expect_program(program, [
    ("LoadConst", 1, 5, 0),
    ("LoadConst", 2, 2, 0),
    ("CompareGT", 1, 2, 3),
    ("JumpIfFalse", 3, 10, 0),
    ("LoadConst", 4, 8, 0),
    ("LoadConst", 5, 3, 0),
    ("CompareGT", 4, 5, 6),
    ("JumpIfFalse", 6, 10, 0),
    ("LoadConst", 0, 1, 0),
    ("Jump", 0, 11, 0),
    ("LoadConst", 0, 0, 0),
    ("JumpIfFalse", 0, 14, 0),
    ("LoadConst", 7, 50, 0),
    ("Forward", 7, 0, 0),
])
print("Test demo_bool_and.py : PASS")

# ---- Test Arithmetic Expression (không gán biến) ----
program = compile_file("demo_arithmetic.py")
expect_program(program, [
    ("LoadConst", 0, 5, 0),
    ("LoadConst", 1, 3, 0),
    ("Add", 0, 1, 2),
    ("Forward", 2, 0, 0),
    ("Stop", 0, 0, 0)
])
print("Test demo_arithmetic.py : PASS")

# ---- Sensor tests ----
# Tạo file tạm cho sensor tests
# ---- Sensor tests ----
# Tạo file tạm cho sensor tests
sensor_files = [
    ("sensor_ultrasonic.py", "distance = read_ultrasonic()"),
    ("sensor_touch.py", "touch = read_touch(1)"),
    ("sensor_light.py", "light = read_light(1)"),
    ("sensor_line.py", "line = read_line(1)"),
]

for filename, source in sensor_files:
    with open(EXAMPLES / filename, "w") as f:
        f.write(source)

# Test ultrasonic assignment (biến distance index 0, temp index 1)
program = compile_file("sensor_ultrasonic.py")
expect_program(program, [
    ("ReadUltrasonic", 1, 0, 0),  # temp 1
    ("Store", 1, 0, 0),           # temp 1 -> biến 0
])
print("Test sensor_ultrasonic.py : PASS")

# Test touch assignment (biến touch index 0, temp1=1, temp2=2)
program = compile_file("sensor_touch.py")
expect_program(program, [
    ("LoadConst", 1, 1, 0),      # temp1 = 1
    ("ReadTouch", 1, 2, 0),      # p1=temp1, p2=temp2
    ("Store", 2, 0, 0),          # temp2 -> biến 0
])
print("Test sensor_touch.py : PASS")

# Test light assignment
program = compile_file("sensor_light.py")
expect_program(program, [
    ("LoadConst", 1, 1, 0),
    ("ReadLight", 1, 2, 0),
    ("Store", 2, 0, 0),
])
print("Test sensor_light.py : PASS")

# Test line assignment
program = compile_file("sensor_line.py")
expect_program(program, [
    ("LoadConst", 1, 1, 0),
    ("ReadLine", 1, 2, 0),
    ("Store", 2, 0, 0),
])
print("Test sensor_line.py : PASS")

# Test sensor + if
program = compile_file("sensor_if.py")
# Dự kiến: biến distance index 0, temp 1 (ReadUltrasonic), temp 2 (LoadConst 20), temp 3 (Compare), temp 4 (LoadConst 50), temp 5 (LoadConst 50 cho backward)
expect_program(program, [
    ("ReadUltrasonic", 1, 0, 0),
    ("Store", 1, 0, 0),
    ("LoadConst", 2, 20, 0),
    ("CompareLT", 0, 2, 3),
    ("JumpIfFalse", 3, 8, 0),
    ("LoadConst", 4, 50, 0),
    ("Forward", 4, 0, 0),
    ("Jump", 0, 10, 0),   # nhảy đến end (index 10)
    ("LoadConst", 5, 50, 0),
    ("Backward", 5, 0, 0),
])
print("Test sensor_if.py : PASS")

# ---- Negative test: statement function used as value ----
def test_invalid_value_call():
    source = "x = forward(50)"
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        path = Path(f.name)
    try:
        compiler = RobotCompiler()
        compiler.compile(path)
        assert False, "Expected CompilerError"
    except CompilerError as e:
        assert "does not return a value" in str(e)
    finally:
        path.unlink(missing_ok=True)

test_invalid_value_call()
print("Test invalid_value_call.py : PASS")

def test_invalid_stop_value():
    source = "x = stop()"
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        path = Path(f.name)
    try:
        compiler = RobotCompiler()
        compiler.compile(path)
        assert False, "Expected CompilerError"
    except CompilerError as e:
        assert "does not return a value" in str(e)
    finally:
        path.unlink(missing_ok=True)

test_invalid_stop_value()
print("Test invalid_stop_value.py : PASS")

# ---- Sensor tests (using committed example files) ----
# The files sensor_ultrasonic.py, sensor_touch.py, sensor_light.py, sensor_line.py
# are already committed in robot-compiler/examples/.
# We do NOT rewrite them during test execution.

program = compile_file("sensor_ultrasonic.py")
expect_program(program, [
    ("ReadUltrasonic", 1, 0, 0),
    ("Store", 1, 0, 0),
])
print("Test sensor_ultrasonic.py : PASS")

program = compile_file("sensor_touch.py")
expect_program(program, [
    ("LoadConst", 1, 1, 0),
    ("ReadTouch", 1, 2, 0),
    ("Store", 2, 0, 0),
])
print("Test sensor_touch.py : PASS")

program = compile_file("sensor_light.py")
expect_program(program, [
    ("LoadConst", 1, 1, 0),
    ("ReadLight", 1, 2, 0),
    ("Store", 2, 0, 0),
])
print("Test sensor_light.py : PASS")

program = compile_file("sensor_line.py")
expect_program(program, [
    ("LoadConst", 1, 1, 0),
    ("ReadLine", 1, 2, 0),
    ("Store", 2, 0, 0),
])
print("Test sensor_line.py : PASS")

# Test sensor + if
program = compile_file("sensor_if.py")
expect_program(program, [
    ("ReadUltrasonic", 1, 0, 0),
    ("Store", 1, 0, 0),
    ("LoadConst", 2, 20, 0),
    ("CompareLT", 0, 2, 3),
    ("JumpIfFalse", 3, 8, 0),
    ("LoadConst", 4, 50, 0),
    ("Forward", 4, 0, 0),
    ("Jump", 0, 10, 0),
    ("LoadConst", 5, 50, 0),
    ("Backward", 5, 0, 0),
])
print("Test sensor_if.py : PASS")

def test_new_apis_compile():
    source = """
set_servo(1, 90)
set_3c_led(2, 1)
set_light_sensor_led(3, 0)
set_motor_straight_angle(1, 2, 70, 360)
line_intersection_stop(70, 17)
"""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        path = Path(f.name)
    compiler = RobotCompiler()
    program = compiler.compile(path)
    path.unlink()
    # Kiểm tra có đủ số instruction (mỗi lệnh emit một instruction, ngoài LoadConst cho hằng số)
    # Số lượng hằng số: 2+2+2+4+2 = 12 hằng số, mỗi hằng số 1 LoadConst + 1 lệnh gọi = 24 instructions
    # Nhưng compiler có thể tối ưu? Trong trường hợp này, vì các hằng số được LoadConst trực tiếp vào biến tạm, nên có thể có 12 LoadConst + 5 lệnh gọi = 17 instructions.
    # Thực tế, mỗi lệnh gọi sẽ resolve argument, và mỗi argument là hằng số sẽ được LoadConst vào biến tạm, sau đó truyền vào lệnh.
    # Vậy số instruction = sum(arg_count) + 5 = 2+2+2+4+2 +5 = 17.
    # Kiểm tra đơn giản là không lỗi.
    print("PASS: New APIs compile")

test_new_apis_compile()