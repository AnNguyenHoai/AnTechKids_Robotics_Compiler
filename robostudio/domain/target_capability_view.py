"""Target-aware capability view for RoboStudio (H26-L)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import json

from tools.runtime_paths import resolve_path

PROFILE_RELATIVE_PATH = ("runtime", "resources", "robot-isa", "target_profiles.json")


def profile_path() -> Path:
    """Resolve the profile from the current application root at call time."""
    return resolve_path(*PROFILE_RELATIVE_PATH)


@dataclass(frozen=True)
class TargetCapabilityView:
    target_id: str
    description: str
    required: tuple[str, ...]
    supported: tuple[str, ...]

    @property
    def missing(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.required) - set(self.supported)))

    @property
    def ready(self) -> bool:
        return not self.missing


class TargetCapabilityViewError(ValueError):
    """Raised when target capability data cannot be consumed by RoboStudio."""


class TargetCapabilityService:
    """Provide a UI-facing view over the canonical H26-K profiles."""

    def __init__(self, profiles: Mapping[str, Mapping]):
        self._profiles = dict(profiles)

    @classmethod
    def load(cls, path: Path | None = None) -> "TargetCapabilityService":
        path = path or profile_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TargetCapabilityViewError(
                f"Unable to load target capability profiles: {exc}"
            ) from exc
        if data.get("schema_version") != 1 or data.get("kind") != "robot_target_capability_profiles":
            raise TargetCapabilityViewError("Invalid target capability profile document")
        profiles = {}
        for item in data.get("profiles", []):
            target_id = item.get("id")
            if not isinstance(target_id, str) or not target_id:
                raise TargetCapabilityViewError("Target profile id must be non-empty")
            profiles[target_id] = item
        return cls(profiles)

    def target_ids(self) -> tuple[str, ...]:
        return tuple(self._profiles)

    def describe(self, target_id: str) -> str:
        profile = self._profiles.get(target_id)
        if profile is None:
            raise TargetCapabilityViewError(f"Unknown target: {target_id}")
        return str(profile.get("description", ""))

    def evaluate(self, target_id: str, required: Iterable[str]) -> TargetCapabilityView:
        profile = self._profiles.get(target_id)
        if profile is None:
            raise TargetCapabilityViewError(f"Unknown target: {target_id}")
        return TargetCapabilityView(
            target_id=target_id,
            description=str(profile.get("description", "")),
            required=tuple(sorted(set(required))),
            supported=tuple(profile.get("capabilities", ())),
        )


API_CAPABILITIES = {
    "forward": "motion.basic", "backward": "motion.basic",
    "turn_left": "motion.basic", "turn_right": "motion.basic",
    "SetMoveRun": "motion.basic", "SetMoveRunSecond": "motion.basic",
    "SetMoveStop": "motion.basic", "set_move_initialize": "motion.basic",
    "set_motor_speed": "motion.speed", "SetMotorSpeed": "motion.speed",
    "set_move_run_angle": "motion.encoder_angle", "SetMoveRunAngle": "motion.encoder_angle",
    "read_ultrasonic": "sensor.ultrasonic", "GetUltrasound": "sensor.ultrasonic",
    "GetUltrasonic": "sensor.ultrasonic", "GetTouch": "sensor.touch",
    "read_line": "sensor.line", "get_trace_value": "sensor.line",
    "get_trace_state": "sensor.line", "get_trace_raw": "sensor.line",
    "line_basis": "line.follow", "line_follow": "line.follow",
    "line_stop": "line.follow", "line_millisecond": "line.follow",
    "SetServo": "actuator.servo", "SetSeeringEngine": "actuator.servo",
    "set_servo": "actuator.servo", "Set3CLed": "actuator.led",
    "set_led": "actuator.led", "set_mp3_play": "peripheral.mp3",
    "SetMp3Play": "peripheral.mp3", "lizard": "peripheral.lizard",
}


def required_capabilities(api_names: Iterable[str]) -> tuple[str, ...]:
    """Translate known source API calls to canonical capability IDs."""
    return tuple(sorted({API_CAPABILITIES[name] for name in api_names if name in API_CAPABILITIES}))
