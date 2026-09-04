# runtime/__init__.py
from .program import RuntimeProgram
from .function import RuntimeFunction
from .instruction import RuntimeInstruction
from .loader import ProgramLoader
from .capability_contract import CapabilityContractError, validate_capabilities
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
from .sensors import (
    ISensor,
    SensorValue,
    SensorEvent,
    SensorEventType,
    SensorManager as NewSensorManager,
    LineSensor,
    UltrasonicSensor,
    TouchSensor,
    LightSensor,
    ColorSensor,
    MovingAverageFilter,
    MedianFilter,
    ThresholdFilter,
    create_mock_sensors,
)

# Keep old SensorManager for backward compatibility, but alias to new one
SensorManager = NewSensorManager

__all__ = [
    "RuntimeProgram",
    "RuntimeFunction",
    "RuntimeInstruction",
    "ProgramLoader",
    "CapabilityContractError",
    "validate_capabilities",
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
    "ISensor",
    "SensorValue",
    "SensorEvent",
    "SensorEventType",
    "LineSensor",
    "UltrasonicSensor",
    "TouchSensor",
    "LightSensor",
    "ColorSensor",
    "MovingAverageFilter",
    "MedianFilter",
    "ThresholdFilter",
    "create_mock_sensors",
    "InvalidBinaryException",
    "UnsupportedVersionException",
    "InvalidInstructionException",
    "InvalidConstantReferenceException",
    "InvalidFunctionReferenceException",
]
