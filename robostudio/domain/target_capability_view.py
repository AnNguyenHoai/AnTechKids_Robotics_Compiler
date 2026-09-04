"""Target-aware capability view for RoboStudio (H26-L)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import json

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "packages" / "robot-isa" / "target_profiles.json"

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
    def load(cls, path: Path = PROFILE_PATH) -> "TargetCapabilityService":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TargetCapabilityViewError(f"Unable to load target capability profiles: {exc}") from exc
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
