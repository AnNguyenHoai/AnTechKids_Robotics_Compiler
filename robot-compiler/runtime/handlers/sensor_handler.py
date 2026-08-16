from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI
from ..value import IntegerValue

def handle_read_ultrasonic(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    dest_idx = ins.operands[0]
    val = api.read_ultrasonic()
    engine.set_variable_by_index(dest_idx, IntegerValue(val))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_read_touch(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    port_idx = ins.operands[0]
    dest_idx = ins.operands[1]
    port_val = engine.get_variable_by_index(port_idx)
    val = api.read_touch(port_val.as_int())
    engine.set_variable_by_index(dest_idx, IntegerValue(val))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_read_light(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    channel_idx = ins.operands[0]
    dest_idx = ins.operands[1]
    channel_val = engine.get_variable_by_index(channel_idx)
    val = api.read_light(channel_val.as_int())
    engine.set_variable_by_index(dest_idx, IntegerValue(val))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_read_line(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    channel_idx = ins.operands[0]
    dest_idx = ins.operands[1]
    channel_val = engine.get_variable_by_index(channel_idx)
    val = api.read_line(channel_val.as_int())
    engine.set_variable_by_index(dest_idx, IntegerValue(val))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_read_color(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    dest_idx = ins.operands[0]
    val = api.read_color()
    engine.set_variable_by_index(dest_idx, IntegerValue(val))
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)