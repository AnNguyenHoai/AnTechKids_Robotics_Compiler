from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from compiler.compiler import RobotCompiler
from compiler.generated.opcode import Opcode

EXAMPLES = ROOT / "examples"
compiler = RobotCompiler()

def compile_file(filename):
    return compiler.compile(EXAMPLES / filename)

def assert_instruction(actual, opcode_name, p1, p2, p3):
    # Lấy tên từ enum bằng giá trị số
    actual_name = Opcode(actual.opcode).name
    assert actual_name == opcode_name, f"Expected {opcode_name}, got {actual_name}"
    assert actual.p1 == p1
    assert actual.p2 == p2
    assert actual.p3 == p3

def expect_program(program, expected):
    assert len(program.instructions) == len(expected), (
        f"Expected {len(expected)} instructions, got {len(program.instructions)}"
    )
    for i, (opcode, p1, p2, p3) in enumerate(expected):
        assert_instruction(program.instructions[i], opcode, p1, p2, p3)

def expect_last_opcode(filename, opcode_name):
    program = compile_file(filename)
    expected_opcode = Opcode[opcode_name].value
    assert program.instructions[-1].opcode == expected_opcode, f"Expected {opcode_name}"

program = compile_file("demo_forward.py")

expect_program(

    program,

    [

        ("LoadConst", 0, 80, 0),

        ("Forward", 0, 0, 0),

        ("Stop", 0, 0, 0)

    ]

)

print("Test demo_forward.py : PASS")


program = compile_file("demo_backward.py")

expect_program(

    program,

    [

        ("LoadConst", 0, 30, 0),

        ("Backward", 0, 0, 0),

        ("Stop", 0, 0, 0)

    ]

)

print("Test demo_backward.py : PASS")

#
# Test : Variable
#

program = compile_file("demo_variable.py")

expect_program(

    program,

    [

        ("LoadConst", 0, 80, 0),

        ("LoadConst", 1, 50, 0),

        ("Forward", 0, 0, 0),

        ("TurnLeft", 1, 0, 0),

        ("Backward", 0, 0, 0),

        ("TurnRight", 1, 0, 0),

        ("Stop", 0, 0, 0)

    ]

)

print("Test demo_variable.py : PASS")


#
# Test : Unknown Function
#

try:

    compile_file("demo_unknown_function.py")

    assert False, "CompilerError expected"

except Exception as e:

    assert "Unknown function" in str(e)

print("Test demo_unknown_function.py : PASS")

#
# Test : Wrong Argument Count
#

try:

    compile_file("demo_wrong_argument.py")

    assert False, "CompilerError expected"

except Exception as e:

    assert "expects exactly 1 argument" in str(e)

print("Test demo_wrong_argument.py : PASS")

program = compile_file(
    "demo_function.py"
)

expect_program(

    program,

    [

        ("LoadConst",0,80,0),

        ("Forward",0,0,0),

        ("Stop",0,0,0)

    ]

)
print("Test demo_function.py : PASS")

program = compile_file(
    "demo_function_multiple.py"
)

expect_program(
    program,
    [
        ("LoadConst",0,80,0),

        ("Forward",0,0,0),

        ("LoadConst",1,80,0),

        ("Forward",1,0,0),
    ]
)
print("Test demo_function_multiple.py : PASS")



program = compile_file(
    "demo_compare_gt.py"
)

expect_last_opcode(
    "demo_compare_gt.py",
    "CompareGT"
)

print("Test CompareGT : PASS")



expect_last_opcode(
    "demo_compare_eq.py",
    "CompareEQ"
)

print("Test CompareEQ : PASS")

expect_last_opcode(
    "demo_compare_ne.py",
    "CompareNE"
)

print("Test CompareNE : PASS")

expect_last_opcode(
    "demo_compare_lt.py",
    "CompareLT"
)

print("Test CompareLT : PASS")

expect_last_opcode(
    "demo_compare_le.py",
    "CompareLE"
)

print("Test CompareLE : PASS")


expect_last_opcode(
    "demo_compare_ge.py",
    "CompareGE"
)

print("Test CompareGE : PASS")


program = compile_file(
    "demo_if.py"
)

expect_program(

    program,

    [

        ("LoadConst", 0, 80, 0),

        ("LoadConst", 1, 50, 0),

        ("CompareGT", 0, 1, 2),

        ("JumpIfFalse", 2, 6, 0),

        ("LoadConst", 3, 80, 0),

        ("Forward", 3, 0, 0),

        ("Stop", 0, 0, 0)

    ]

)

print("Test demo_if.py : PASS")

program = compile_file(
    "demo_if_else.py"
)

expect_program(

    program,

    [

        ("LoadConst",0,80,0),

        ("LoadConst",1,50,0),

        ("CompareGT",0,1,2),

        ("JumpIfFalse",2,7,0),

        ("LoadConst",3,80,0),

        ("Forward",3,0,0),

        ("Jump",0,9,0),

        ("LoadConst",4,30,0),

        ("Backward",4,0,0),

        ("Stop",0,0,0)

    ]

)

print("Test demo_if_else.py : PASS")

program = compile_file(
    "demo_nested_if.py"
)

expect_program(

    program,

    [

        ("LoadConst",0,80,0),

        ("LoadConst",1,40,0),

        ("LoadConst",2,50,0),

        ("CompareGT",0,2,3),

        ("JumpIfFalse",3,10,0),

        ("LoadConst",4,60,0),

        ("CompareLT",1,4,5),

        ("JumpIfFalse",5,10,0),

        ("LoadConst",6,80,0),

        ("Forward",6,0,0),

        ("Stop",0,0,0)

    ]

)
print("demo_nested_if.py : PASS")

program = compile_file(
    "demo_while.py"
)

expect_program(

    program,

    [

        ("LoadConst",0,80,0),

        ("LoadConst",1,50,0),

        ("CompareGT",0,1,2),

        ("JumpIfFalse",2,7,0),

        ("LoadConst",3,80,0),

        ("Forward",3,0,0),

        ("Jump",0,1,0),

        ("Stop",0,0,0)

    ]

)

print("Test demo_while.py : PASS") 

program = compile_file(
    "demo_nested_while.py"
)

program = compile_file(
    "demo_nested_while.py"
)

expect_program(

    program,

    [

        ("LoadConst",0,80,0),

        ("LoadConst",1,40,0),

        ("LoadConst",2,50,0),

        ("CompareGT",0,2,3),

        ("JumpIfFalse",3,12,0),

        ("LoadConst",4,60,0),

        ("CompareLT",1,4,5),

        ("JumpIfFalse",5,11,0),

        ("LoadConst",6,80,0),

        ("Forward",6,0,0),

        ("Jump",0,5,0),

        ("Jump",0,2,0),

        ("Stop",0,0,0)

    ]

)

print("Test demo_nested_while.py : PASS")

program = compile_file(
    "demo_break.py"
)

expect_program(

    program,

    [

        ("LoadConst",0,80,0),

        ("LoadConst",1,50,0),

        ("CompareGT",0,1,2),

        ("JumpIfFalse",2,8,0),

        ("LoadConst",3,80,0),

        ("Forward",3,0,0),

        ("Jump",0,8,0),

        ("Jump",0,1,0),

        ("Stop",0,0,0)

    ]

)
print("Test demo_break.py : PASS")


program = compile_file(
    "demo_continue.py"
)

print("Test demo_continue.py : PASS")

program = compile_file("demo_bool_and.py")

program = compile_file(
    "demo_bool_and.py"
)

expect_program(

    program,

    [

        ("LoadConst",1,5,0),

        ("LoadConst",2,2,0),

        ("CompareGT",1,2,3),

        ("JumpIfFalse",3,10,0),

        ("LoadConst",4,8,0),

        ("LoadConst",5,3,0),

        ("CompareGT",4,5,6),

        ("JumpIfFalse",6,10,0),

        ("LoadConst",0,1,0),

        ("Jump",0,11,0),

        ("LoadConst",0,0,0),

        ("JumpIfFalse",0,14,0),

        ("LoadConst",7,50,0),

        ("Forward",7,0,0),

    ]

)

print("Test demo_bool_and.py : PASS")

