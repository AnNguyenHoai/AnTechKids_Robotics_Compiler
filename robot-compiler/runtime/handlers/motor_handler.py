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

def _resolve_arg(engine, index):
    return engine.get_variable_by_index(index).as_int()


def handle_line_basis(ins, engine, api):
    api.line_basis(_resolve_arg(engine, ins.operands[0]))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)


def handle_line_follow(ins, engine, api):
    api.line_follow(_resolve_arg(engine, ins.operands[0]))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)


def handle_line_stop(ins, engine, api):
    api.line_stop()
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)


def handle_line_millisecond(ins, engine, api):
    api.line_millisecond(
        _resolve_arg(engine, ins.operands[0]),
        _resolve_arg(engine, ins.operands[1]),
    )
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)
