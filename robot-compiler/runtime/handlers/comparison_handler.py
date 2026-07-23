# runtime/handlers/comparison_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

COMPARE_OP = {
    "CompareEQ": "==",
    "CompareNE": "!=",
    "CompareLT": "<",
    "CompareLE": "<=",
    "CompareGT": ">",
    "CompareGE": ">=",
}

def handle_compare(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    left_idx = ins.operands[0]
    right_idx = ins.operands[1]
    result_idx = ins.operands[2]
    left = engine.get_variable_by_index(left_idx)
    right = engine.get_variable_by_index(right_idx)
    op = COMPARE_OP[ins.opcode.name]
    result = engine.compare(left, right, op)
    engine.set_variable_by_index(result_idx, result)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)