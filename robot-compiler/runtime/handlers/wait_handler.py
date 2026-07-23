# runtime/handlers/wait_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

def handle_wait(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    duration_idx = ins.operands[0]
    duration_val = engine.get_variable_by_index(duration_idx)
    api.wait(duration_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)