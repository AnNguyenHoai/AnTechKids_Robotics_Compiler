"""Persistent RoboStudio registry for multiple physical robots.

H30 keeps robot identity keyed by the stable H27 ``device_id``. Discovery is
an observation cycle, not the source of truth for whether a robot is known:
robots remain registered when offline and a later discovery refreshes their
last-known network/firmware/capability snapshot without creating duplicates.

Only durable identity/last-seen state is written to disk. ``online`` is an
in-memory observation and always starts false after a RoboStudio restart.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from services.robot_discovery_service import RobotInfo, serialize_robot_info, validate_robot_info
from tools import runtime_paths

REGISTRY_TYPE = "antechkids.robostudio.robot-registry"
REGISTRY_SCHEMA = 1
REGISTRY_FILENAME = "robot_registry.json"


class RobotRegistryError(RuntimeError):
    """Raised when persistent robot state cannot be read or written safely."""


@dataclass(frozen=True)
class ManagedRobot:
    """One known robot plus the current discovery-cycle availability state."""

    robot: RobotInfo
    online: bool = False
    last_seen_utc: str = ""

    @property
    def device_id(self) -> str:
        return self.robot.device_id

    @property
    def display_label(self) -> str:
        return self.robot.display_label


class RobotRegistryService:
    """Own the persistent multi-robot registry and selected robot identity."""

    def __init__(
        self,
        path: Path | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = Path(path or self._default_path()).expanduser().resolve()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._robots: dict[str, ManagedRobot] = {}
        self._selected_device_id: str | None = None
        self.load_error: str | None = None
        self._load()

    @staticmethod
    def _default_path() -> Path:
        root = runtime_paths.prepare_user_data_root()
        return root / "robots" / REGISTRY_FILENAME

    @property
    def selected_device_id(self) -> str | None:
        return self._selected_device_id

    def robots(self) -> tuple[ManagedRobot, ...]:
        """Return online robots first, then deterministic display-name ordering."""
        return tuple(
            sorted(
                self._robots.values(),
                key=lambda item: (not item.online, item.display_label.lower(), item.device_id),
            )
        )

    def get(self, device_id: str | None) -> ManagedRobot | None:
        if not device_id:
            return None
        return self._robots.get(device_id)

    def selected(self) -> ManagedRobot | None:
        return self.get(self._selected_device_id)

    def online_count(self) -> int:
        return sum(1 for item in self._robots.values() if item.online)

    def set_selected(self, device_id: str | None) -> None:
        if device_id is not None and device_id not in self._robots:
            raise RobotRegistryError(f"Cannot select unknown robot: {device_id}")
        if device_id == self._selected_device_id:
            return
        self._selected_device_id = device_id
        self._save()

    def mark_all_offline(self) -> tuple[ManagedRobot, ...]:
        """Begin a discovery cycle without deleting any known robot."""
        self._robots = {
            device_id: ManagedRobot(item.robot, False, item.last_seen_utc)
            for device_id, item in self._robots.items()
        }
        return self.robots()

    def upsert(self, robot: RobotInfo, *, online: bool = True) -> ManagedRobot:
        """Add/update one robot by stable device_id, including IP changes."""
        previous = self._robots.get(robot.device_id)
        last_seen = self._now_iso() if online else (previous.last_seen_utc if previous else "")
        item = ManagedRobot(robot=robot, online=online, last_seen_utc=last_seen)
        self._robots[robot.device_id] = item
        self._save()
        return item

    def merge_discovery(self, discovered: Iterable[RobotInfo]) -> tuple[ManagedRobot, ...]:
        """Merge one complete discovery observation into persistent state.

        Every previously known robot is retained. Robots absent from the current
        successful discovery become offline. Repeated packets or IP changes for
        the same ``device_id`` update one record rather than creating another.
        """
        now = self._now_iso()
        next_state: dict[str, ManagedRobot] = {
            device_id: ManagedRobot(item.robot, False, item.last_seen_utc)
            for device_id, item in self._robots.items()
        }
        for robot in discovered:
            next_state[robot.device_id] = ManagedRobot(
                robot=robot,
                online=True,
                last_seen_utc=now,
            )
        self._robots = next_state
        if self._selected_device_id and self._selected_device_id not in self._robots:
            self._selected_device_id = None
        self._save()
        return self.robots()

    def _now_iso(self) -> str:
        value = self._clock()
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("registry root must be an object")
            if data.get("type") != REGISTRY_TYPE:
                raise ValueError("unsupported robot registry type")
            if data.get("schema_version") != REGISTRY_SCHEMA:
                raise ValueError("unsupported robot registry schema")
            entries = data.get("robots")
            if not isinstance(entries, list):
                raise ValueError("robots must be a list")

            loaded: dict[str, ManagedRobot] = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("robot registry entry must be an object")
                info = validate_robot_info(entry.get("info"))
                last_seen = entry.get("last_seen_utc", "")
                if not isinstance(last_seen, str):
                    raise ValueError("last_seen_utc must be a string")
                if info.device_id in loaded:
                    raise ValueError(f"duplicate robot device_id: {info.device_id}")
                # Availability is deliberately not persisted across application restarts.
                loaded[info.device_id] = ManagedRobot(info, False, last_seen)

            selected = data.get("selected_device_id")
            if selected is not None and not isinstance(selected, str):
                raise ValueError("selected_device_id must be a string or null")
            if selected and selected not in loaded:
                selected = None

            self._robots = loaded
            self._selected_device_id = selected or None
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            # A damaged preference file must not prevent RoboStudio from opening.
            # Keep the error observable to the UI/tests and start with an empty,
            # fail-safe registry; the next explicit save replaces the bad file.
            self._robots = {}
            self._selected_device_id = None
            self.load_error = f"Unable to load robot registry {self.path}: {exc}"

    def _save(self) -> None:
        payload = {
            "type": REGISTRY_TYPE,
            "schema_version": REGISTRY_SCHEMA,
            "selected_device_id": self._selected_device_id,
            "robots": [
                {
                    "last_seen_utc": item.last_seen_utc,
                    "info": serialize_robot_info(item.robot),
                }
                for item in sorted(self._robots.values(), key=lambda value: value.device_id)
            ],
        }
        temp_path = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            os.replace(temp_path, self.path)
            self.load_error = None
        except OSError as exc:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise RobotRegistryError(f"Unable to save robot registry {self.path}: {exc}") from exc
