# runtime/handlers/jump_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

def handle_jump(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    target = ins.operands[0]
    print(f"[Jump] target={target}")
    engine.jump(target)

def handle_jump_if_false(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    cond_idx = ins.operands[0]
    target = ins.operands[1]
    cond_val = engine.get_variable_by_index(cond_idx)
    print(f"[JumpIfFalse] cond_idx={cond_idx}, cond_val={cond_val.as_bool()}, target={target}")
    if not cond_val.as_bool():
        engine.jump(target)
    else:
        engine.context.program_counter += 1
        engine.iterator.seek(engine.context.program_counter)

def handle_jump_if_true(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    cond_idx = ins.operands[0]
    target = ins.operands[1]
    cond_val = engine.get_variable_by_index(cond_idx)
    if cond_val.as_bool():
        engine.jump(target)
    else:
        engine.context.program_counter += 1
        engine.iterator.seek(engine.context.program_counter)