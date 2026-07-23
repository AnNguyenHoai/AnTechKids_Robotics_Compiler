# runtime/handlers/arithmetic_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

ARITH_OP = {
    "Add": "add",
    "Sub": "sub",
    "Mul": "mul",
    "Div": "div",
    "Mod": "mod",
    "Pow": "pow",
    "Neg": "neg",
}

def handle_arithmetic(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    op = ins.opcode
    if op.name == "Neg":
        src_idx = ins.operands[0]
        result_idx = ins.operands[1]
        val = engine.get_variable_by_index(src_idx)
        result = engine.neg(val)
        engine.set_variable_by_index(result_idx, result)
    else:
        left_idx = ins.operands[0]
        right_idx = ins.operands[1]
        result_idx = ins.operands[2]
        left = engine.get_variable_by_index(left_idx)
        right = engine.get_variable_by_index(right_idx)
        op_name = op.name
        if op_name == "Add":
            result = engine.add(left, right)
        elif op_name == "Sub":
            result = engine.sub(left, right)
        elif op_name == "Mul":
            result = engine.mul(left, right)
        elif op_name == "Div":
            result = engine.div(left, right)
        elif op_name == "Mod":
            result = engine.mod(left, right)
        elif op_name == "Pow":
            result = engine.pow(left, right)
        else:
            raise ValueError(f"Unknown arithmetic op: {op_name}")
        engine.set_variable_by_index(result_idx, result)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_load_const(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    var_idx = ins.operands[0]
    const_val = ins.operands[1]  # hằng số có thể là int, float, string, bool
    # Tạo RuntimeValue tương ứng
    if isinstance(const_val, int):
        from ..value import IntegerValue
        val = IntegerValue(const_val)
    elif isinstance(const_val, float):
        from ..value import FloatValue
        val = FloatValue(const_val)
    elif isinstance(const_val, str):
        from ..value import StringValue
        val = StringValue(const_val)
    elif isinstance(const_val, bool):
        from ..value import BooleanValue
        val = BooleanValue(const_val)
    else:
        raise TypeError(f"Unsupported constant type: {type(const_val)}")
    engine.set_variable_by_index(var_idx, val)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_store(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    src_idx = ins.operands[0]
    dest_idx = ins.operands[1]
    val = engine.get_variable_by_index(src_idx)
    engine.set_variable_by_index(dest_idx, val)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)