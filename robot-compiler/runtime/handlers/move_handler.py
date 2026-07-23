# runtime/handlers/move_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI
from compiler.generated.opcode import Opcode

def handle_forward(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    api.forward(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_backward(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    api.backward(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_turn_left(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    api.left(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_turn_right(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    api.right(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_stop(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    api.stop()
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)