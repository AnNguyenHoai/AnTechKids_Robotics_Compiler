"""H26-K target capability profiles.

A target profile is the runtime-facing capability declaration for a concrete
execution target. Profiles are data-driven so adding a target does not require
changing VM or capability-contract logic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PROFILE_PATH = _ROOT / "packages" / "robot-isa" / "target_profiles.json"


class TargetProfileError(ValueError):
    """Raised when a target capability profile is invalid or unknown."""


@dataclass(frozen=True)
class TargetCapabilityProfile:
    target_id: str
    description: str
    capabilities: tuple[str, ...]

    def supports(self, capability_id: str) -> bool:
        return capability_id in self.capabilities

    def supports_all(self, required: Iterable[str]) -> bool:
        supported = set(self.capabilities)
        return set(required).issubset(supported)


class TargetCapabilityRegistry:
    """Loads and validates immutable target capability profiles."""

    def __init__(self, profiles: Mapping[str, TargetCapabilityProfile]):
        self._profiles = dict(profiles)

    @classmethod
    def load(cls, path: Path = _DEFAULT_PROFILE_PATH) -> "TargetCapabilityRegistry":
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise TargetProfileError("Unsupported target profile schema version")
        if data.get("kind") != "robot_target_capability_profiles":
            raise TargetProfileError("Invalid target profile document kind")

        profiles: dict[str, TargetCapabilityProfile] = {}
        for item in data.get("profiles", []):
            target_id = item.get("id")
            capabilities = item.get("capabilities")
            if not isinstance(target_id, str) or not target_id:
                raise TargetProfileError("Target profile id must be a non-empty string")
            if target_id in profiles:
                raise TargetProfileError(f"Duplicate target profile: {target_id}")
            if not isinstance(capabilities, list) or any(
                not isinstance(capability, str) or not capability
                for capability in capabilities
            ):
                raise TargetProfileError(
                    f"Target profile '{target_id}' capabilities must be a list of strings"
                )
            if len(set(capabilities)) != len(capabilities):
                raise TargetProfileError(
                    f"Target profile '{target_id}' contains duplicate capabilities"
                )
            profiles[target_id] = TargetCapabilityProfile(
                target_id=target_id,
                description=str(item.get("description", "")),
                capabilities=tuple(capabilities),
            )
        return cls(profiles)

    def get(self, target_id: str) -> TargetCapabilityProfile:
        try:
            return self._profiles[target_id]
        except KeyError as exc:
            raise TargetProfileError(f"Unknown target profile: {target_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(self._profiles)

    def validate_program(self, target_id: str, required_capabilities: Iterable[str]) -> None:
        profile = self.get(target_id)
        missing = sorted(set(required_capabilities) - set(profile.capabilities))
        if missing:
            raise TargetProfileError(
                f"Target '{target_id}' does not support required capabilities: "
                + ", ".join(missing)
            )
