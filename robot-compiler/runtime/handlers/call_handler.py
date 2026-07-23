# runtime/handlers/call_handler.py
from ..instruction import RuntimeInstruction
from ..engine import ExecutionEngine
from ..mock.robot_api import MockRobotAPI

def handle_call(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    func_id = ins.operands[0]
    engine.call(func_id)

def handle_return(ins: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
    engine.return_()