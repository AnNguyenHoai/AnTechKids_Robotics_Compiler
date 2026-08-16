from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

def handle_set_motor_speed(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    left_idx = ins.operands[0]
    right_idx = ins.operands[1]
    left = engine.get_variable_by_index(left_idx).as_int()
    right = engine.get_variable_by_index(right_idx).as_int()
    api.set_motor_speed(left, right)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)