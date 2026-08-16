from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

def handle_set_3c_led(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    port_idx = ins.operands[0]
    state_idx = ins.operands[1]
    port = engine.get_variable_by_index(port_idx).as_int()
    state = engine.get_variable_by_index(state_idx).as_int()
    api.set_led(port, state)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_set_light_sensor_led(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    port_idx = ins.operands[0]
    state_idx = ins.operands[1]
    port = engine.get_variable_by_index(port_idx).as_int()
    state = engine.get_variable_by_index(state_idx).as_int()
    api.set_led(port, state)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)

def handle_set_mp3_play(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    index_idx = ins.operands[0]
    index = engine.get_variable_by_index(index_idx).as_int()
    api.set_mp3_play(index)
    engine.context.program_counter += 1
    engine.iterator.seek(engine.context.program_counter)