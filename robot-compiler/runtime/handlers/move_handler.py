# runtime/handlers/move_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..robot import IRobot

def handle_forward(ins: RuntimeInstruction, engine: ExecutionEngine, robot: IRobot):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    robot.forward(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_backward(ins: RuntimeInstruction, engine: ExecutionEngine, robot: IRobot):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    robot.backward(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_turn_left(ins: RuntimeInstruction, engine: ExecutionEngine, robot: IRobot):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    robot.left(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_turn_right(ins: RuntimeInstruction, engine: ExecutionEngine, robot: IRobot):
    speed_idx = ins.operands[0]
    speed_val = engine.get_variable_by_index(speed_idx)
    robot.right(speed_val.as_int())
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_stop(ins: RuntimeInstruction, engine: ExecutionEngine, robot: IRobot):
    robot.stop()
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)