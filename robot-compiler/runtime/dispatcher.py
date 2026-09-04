# runtime/dispatcher.py
from typing import Dict, Callable
from compiler.generated.opcode import Opcode
from .instruction import RuntimeInstruction
from .engine import ExecutionEngine
from .robot import IRobot
from .handlers import (
    move_handler, wait_handler, jump_handler, call_handler,
    comparison_handler, arithmetic_handler
)
# Import các handler mới
from .handlers import sensor_handler, led_handler, motor_handler

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
            # Thêm các handler mới
            Opcode.ReadUltrasonic: sensor_handler.handle_read_ultrasonic,
            Opcode.ReadTouch: sensor_handler.handle_read_touch,
            Opcode.ReadLight: sensor_handler.handle_read_light,
            Opcode.ReadLine: sensor_handler.handle_read_line,
            Opcode.GetTraceValue: sensor_handler.handle_get_trace_value,
            Opcode.GetTraceState: sensor_handler.handle_get_trace_state,
            Opcode.GetTraceRaw: sensor_handler.handle_get_trace_raw,
            Opcode.ReadColor: sensor_handler.handle_read_color,
            Opcode.Set3CLed: led_handler.handle_set_3c_led,
            Opcode.SetLightSensorLed: led_handler.handle_set_light_sensor_led,
            Opcode.SetMp3Play: led_handler.handle_set_mp3_play,
            Opcode.SetMotorSpeed: motor_handler.handle_set_motor_speed,
            Opcode.LineBasis: motor_handler.handle_line_basis,
            Opcode.LineFollow: motor_handler.handle_line_follow,
            Opcode.LineStop: motor_handler.handle_line_stop,
            Opcode.LineMillisecond: motor_handler.handle_line_millisecond,
        }

    def dispatch(self, instruction: RuntimeInstruction, engine: ExecutionEngine, robot: IRobot):
        handler = self.handlers.get(instruction.opcode)
        if handler is None:
            raise ValueError(f"No handler for opcode {instruction.opcode}")
        handler(instruction, engine, robot)