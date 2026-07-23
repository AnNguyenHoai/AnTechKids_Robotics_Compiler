# runtime/dispatcher.py
from typing import Dict, Callable
from compiler.generated.opcode import Opcode
from .instruction import RuntimeInstruction
from .engine import ExecutionEngine
from .mock.robot_api import MockRobotAPI
from .handlers import (
    move_handler, wait_handler, jump_handler, call_handler,
    comparison_handler, arithmetic_handler
)

class Dispatcher:
    def __init__(self):
        self.handlers: Dict[Opcode, Callable] = {
            Opcode.Forward: move_handler.handle_forward,
            Opcode.Backward: move_handler.handle_backward,
            Opcode.TurnLeft: move_handler.handle_turn_left,
            Opcode.TurnRight: move_handler.handle_turn_right,
            Opcode.Wait: wait_handler.handle_wait,
            Opcode.Stop: move_handler.handle_stop,
            Opcode.Jump: jump_handler.handle_jump,
            Opcode.JumpIfFalse: jump_handler.handle_jump_if_false,
            Opcode.JumpIfTrue: jump_handler.handle_jump_if_true,
            Opcode.Call: call_handler.handle_call,
            Opcode.Return: call_handler.handle_return,
            Opcode.CompareEQ: comparison_handler.handle_compare,
            Opcode.CompareNE: comparison_handler.handle_compare,
            Opcode.CompareLT: comparison_handler.handle_compare,
            Opcode.CompareLE: comparison_handler.handle_compare,
            Opcode.CompareGT: comparison_handler.handle_compare,
            Opcode.CompareGE: comparison_handler.handle_compare,
            Opcode.Add: arithmetic_handler.handle_arithmetic,
            Opcode.Sub: arithmetic_handler.handle_arithmetic,
            Opcode.Mul: arithmetic_handler.handle_arithmetic,
            Opcode.Div: arithmetic_handler.handle_arithmetic,
            Opcode.Mod: arithmetic_handler.handle_arithmetic,
            Opcode.Pow: arithmetic_handler.handle_arithmetic,
            Opcode.Neg: arithmetic_handler.handle_arithmetic,
            Opcode.LoadConst: arithmetic_handler.handle_load_const,
            Opcode.Store: arithmetic_handler.handle_store,
        }

    def dispatch(self, instruction: RuntimeInstruction, engine: ExecutionEngine, api: MockRobotAPI):
        handler = self.handlers.get(instruction.opcode)
        if handler is None:
            raise ValueError(f"No handler for opcode {instruction.opcode}")
        handler(instruction, engine, api)