"""Hardware capability requirements for RoboStudio programs (H25-F)."""

from dataclasses import dataclass
from typing import Dict, FrozenSet, Iterable, Tuple


@dataclass(frozen=True)
class HardwareRequirement:
    """Hardware required by one public Robot API."""
    api_name: str
    devices: FrozenSet[str]
    description: str = ""


class HardwareRequirementRegistry:
    """Maps Robot API names to required hardware devices.

    API names are canonical snake_case names. The validator also accepts legacy
    RoboSim/RCU aliases so H25-F works with existing user programs.
    """

    _REQUIREMENTS: Dict[str, HardwareRequirement] = {}

    @classmethod
    def _register(cls, devices: Iterable[str], *names: str, description: str = "") -> None:
        required = frozenset(devices)
        for name in names:
            cls._REQUIREMENTS[name] = HardwareRequirement(name, required, description)

    @classmethod
    def required_devices(cls, api_name: str) -> FrozenSet[str]:
        requirement = cls._REQUIREMENTS.get(api_name)
        return requirement.devices if requirement else frozenset()

    @classmethod
    def known_api_names(cls) -> Tuple[str, ...]:
        return tuple(cls._REQUIREMENTS.keys())


# Drive motion
HardwareRequirementRegistry._register(
    ("motor",),
    "forward", "backward", "turn_left", "turn_right",
    "set_motor_speed", "set_move_initialize", "set_move_run_angle",
    "set_motor", "set_motor_servo", "set_motor_straight_angle",
    "SetMoveRun", "SetMoveRunSecond", "SetMoveRunAngle", "SetMoveStop",
    "SetMotor", "SetMotorSpeed",
    description="Drive motion requires the main motors.",
)

# Line sensing and line behavior
HardwareRequirementRegistry._register(
    ("line_sensor",),
    "read_line", "get_trace_value", "get_trace_state", "get_trace_raw",
    "get_light_sensor_data",
    "GetTraceValue", "GetTraceV2I2CChxState", "GetTraceRaw",
    description="Trace APIs require the line sensor.",
)
HardwareRequirementRegistry._register(
    ("motor", "line_sensor"),
    "line_basis", "line_follow", "line_stop", "line_millisecond",
    "line_intersection_stop", "line_turn_encounterline", "line_for_bmp",
    "line_set_initialize",
    "LineBasis", "LineFollow", "LineStop", "LineMillisecond",
    "LineIntersectionStop", "LineTurnEncounterLine", "LineForBmp",
    description="Line following requires both motors and the line sensor.",
)

# Ultrasonic
HardwareRequirementRegistry._register(
    ("ultrasonic",),
    "read_ultrasonic", "GetUltrasound", "GetUltrasonic",
    description="Distance reading requires the ultrasonic sensor.",
)

# Servo
HardwareRequirementRegistry._register(
    ("servo",),
    "set_servo", "set_seering_engine", "set_seering_engine_time",
    "SetServo", "SetSeeringEngine", "SetSeeringEngineTime",
    description="Servo control requires servo hardware.",
)

# Buzzer
HardwareRequirementRegistry._register(
    ("buzzer",),
    "set_mp3_play", "SetMp3Play",
    description="Audio output requires the buzzer.",
)
