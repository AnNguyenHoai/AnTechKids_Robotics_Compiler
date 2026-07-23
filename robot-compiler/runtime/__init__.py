# runtime/__init__.py
from .program import RuntimeProgram
from .function import RuntimeFunction
from .instruction import RuntimeInstruction
from .loader import ProgramLoader
from .iterator import InstructionIterator
from .exceptions import *
from .context import ExecutionContext, ExecutionState
from .dispatcher import Dispatcher
from .vm import VirtualMachine
from .mock.robot_api import MockRobotAPI
from .engine import ExecutionEngine
from .variable import VariableTable
from .stack import DataStack
from .frame import StackFrame
from .value import *
from .memory import MemoryManager
from .robot import RobotRuntime, MotionController, SensorManager, RobotState, IRobot
from .hardware import (
    IHardware,
    MockHardware,
    IMotorDriver,
    ITimer,
    ILogger,
    ESP32Hardware,
    BoardConfiguration,
    HardwareCapabilities,
    ESP32MotorDriver,
    ESP32Timer,
    ESP32Logger,
)

__all__ = [
    "RuntimeProgram",
    "RuntimeFunction",
    "RuntimeInstruction",
    "ProgramLoader",
    "InstructionIterator",
    "ExecutionContext",
    "ExecutionState",
    "Dispatcher",
    "VirtualMachine",
    "MockRobotAPI",
    "ExecutionEngine",
    "VariableTable",
    "DataStack",
    "StackFrame",
    "RuntimeValue",
    "IntegerValue",
    "FloatValue",
    "BooleanValue",
    "StringValue",
    "ReferenceValue",
    "MemoryManager",
    "RobotRuntime",
    "MotionController",
    "SensorManager",
    "RobotState",
    "IRobot",
    "IHardware",
    "MockHardware",
    "IMotorDriver",
    "ITimer",
    "ILogger",
    "ESP32Hardware",
    "BoardConfiguration",
    "HardwareCapabilities",
    "ESP32MotorDriver",
    "ESP32Timer",
    "ESP32Logger",
    "InvalidBinaryException",
    "UnsupportedVersionException",
    "InvalidInstructionException",
    "InvalidConstantReferenceException",
    "InvalidFunctionReferenceException",
]