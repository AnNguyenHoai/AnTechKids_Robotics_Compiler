#!/usr/bin/env python3
"""EPIC H30 Multi-Robot Management regression contract."""
from __future__ import annotations

import ast
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
for path in (str(ROOT), str(ROBOSTUDIO)):
    if path not in sys.path:
        sys.path.insert(0, path)

from services.robot_deployment_service import select_unique_new_robot
from services.robot_discovery_service import RobotInfo, serialize_robot_info, validate_robot_info
from services.robot_registry_service import RobotRegistryService


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS: {label}")


def robot(device_id: str, ip: str, *, name: str | None = None) -> RobotInfo:
    suffix = device_id.replace("robot-", "")[-6:]
    return RobotInfo(
        device_id=device_id,
        name=name or f"AnTechKids Robot {suffix}",
        hostname=f"robot-{suffix.lower()}",
        ip=ip,
        target="esp32",
        firmware="0.1.1",
        robot_ready=True,
        network_ready=True,
        ready=True,
        ota=True,
        capabilities={"motor": True, "line_sensor": True, "ultrasonic": False},
    )


def fixed_clock() -> datetime:
    return datetime(2026, 9, 19, 8, 30, 0, tzinfo=timezone.utc)


def test_registry_persists_multiple_robots_and_selection() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "robot_registry.json"
        first = RobotRegistryService(path, clock=fixed_clock)
        r1 = robot("robot-AAA111", "192.168.1.21")
        r2 = robot("robot-BBB222", "192.168.1.22")
        first.merge_discovery([r1, r2])
        first.set_selected(r2.device_id)
        check(len(first.robots()) == 2, "registry stores multiple robots")
        check(first.online_count() == 2, "discovered robots are online in current session")

        restarted = RobotRegistryService(path, clock=fixed_clock)
        check(len(restarted.robots()) == 2, "known robots survive RoboStudio restart")
        check(restarted.online_count() == 0, "online state is not falsely persisted across restart")
        check(restarted.selected_device_id == r2.device_id, "selected device_id survives restart")
        check(restarted.selected() is not None and not restarted.selected().online,
              "selected offline robot remains addressable by stable identity")


def test_ip_change_updates_same_identity_without_duplicate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "robot_registry.json"
        service = RobotRegistryService(path, clock=fixed_clock)
        original = robot("robot-CCC333", "192.168.1.30")
        moved = robot("robot-CCC333", "192.168.1.77")
        service.merge_discovery([original])
        service.merge_discovery([moved])
        items = service.robots()
        check(len(items) == 1, "IP change does not duplicate a stable device_id")
        check(items[0].robot.ip == "192.168.1.77", "latest discovered IP replaces last-known IP")


def test_discovery_merge_retains_offline_robots() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "robot_registry.json"
        service = RobotRegistryService(path, clock=fixed_clock)
        r1 = robot("robot-DDD444", "192.168.1.41")
        r2 = robot("robot-EEE555", "192.168.1.42")
        service.merge_discovery([r1, r2])
        service.set_selected(r1.device_id)
        service.merge_discovery([robot(r2.device_id, "192.168.1.99")])
        first = service.get(r1.device_id)
        second = service.get(r2.device_id)
        check(first is not None and not first.online, "robot absent from successful scan becomes Offline, not deleted")
        check(second is not None and second.online, "robot present in successful scan remains Online")
        check(service.selected_device_id == r1.device_id, "offline selected robot identity is retained")


def test_duplicate_discovery_packets_collapse_by_device_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "robot_registry.json"
        service = RobotRegistryService(path, clock=fixed_clock)
        old = robot("robot-FFF666", "192.168.1.50")
        new = robot("robot-FFF666", "192.168.1.51")
        service.merge_discovery([old, new])
        check(len(service.robots()) == 1, "duplicate discovery identities collapse to one registry record")
        check(service.robots()[0].robot.ip == new.ip, "last observation wins within one discovery cycle")


def test_corrupt_registry_fails_safe_and_recovers_on_save() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "robot_registry.json"
        path.write_text("{ definitely not json", encoding="utf-8")
        service = RobotRegistryService(path, clock=fixed_clock)
        check(service.load_error is not None, "corrupt registry is observable")
        check(service.robots() == (), "corrupt registry does not create phantom robots")
        service.upsert(robot("robot-GGG777", "192.168.1.61"), online=True)
        payload = json.loads(path.read_text(encoding="utf-8"))
        check(payload["schema_version"] == 1 and len(payload["robots"]) == 1,
              "next explicit save atomically replaces corrupt registry")


def test_identity_serialization_roundtrip() -> None:
    original = robot("robot-HHH888", "192.168.1.71")
    restored = validate_robot_info(serialize_robot_info(original))
    check(restored == original, "persistent identity snapshot round-trips through canonical H27 schema")


def test_first_flash_never_binds_arbitrary_existing_robot() -> None:
    r1 = robot("robot-III999", "192.168.1.81")
    r2 = robot("robot-JJJ000", "192.168.1.82")
    r3 = robot("robot-KKK111", "192.168.1.83")
    r4 = robot("robot-LLL222", "192.168.1.84")
    known = {r1.device_id, r2.device_id}
    check(select_unique_new_robot(known, [r1, r2, r3]) == r3,
          "first flash auto-binds exactly one newly appeared device_id")
    check(select_unique_new_robot(known, [r1, r2]) is None,
          "first flash does not claim an existing robot")
    check(select_unique_new_robot(known, [r1, r2, r3, r4]) is None,
          "first flash refuses ambiguous multiple new robots")


def has_positional_robot_zero_index(source: str) -> bool:
    """Detect executable ``robots[0]`` access without matching comments/strings."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        if not isinstance(node.value, ast.Name) or node.value.id != "robots":
            continue
        index = node.slice
        if isinstance(index, ast.Constant) and index.value == 0:
            return True
    return False


def test_ui_and_runtime_contract_source() -> None:
    ui = (ROOT / "robostudio" / "ui" / "robot_tab.py").read_text(encoding="utf-8")
    deploy = (ROOT / "robostudio" / "services" / "robot_deployment_service.py").read_text(encoding="utf-8")
    registry = (ROOT / "robostudio" / "services" / "robot_registry_service.py").read_text(encoding="utf-8")
    check("RobotRegistryService" in ui, "Robot tab consumes persistent registry service")
    check("Offline" in ui and "Online" in ui, "Robot tab exposes Online/Offline state")
    check("item.online" in ui, "OTA Run is gated by live discovery state")
    check("self._robots = []" not in ui, "Discover no longer destroys known robot state")
    check(not has_positional_robot_zero_index(deploy),
          "first-flash path no longer binds first discovered robot")
    check("selected_device_id" in registry and "device_id" in registry,
          "registry persistence is keyed by stable device identity")
    check("prepare_user_data_root" in registry,
          "robot registry lives in external writable RoboStudio state")


def main() -> int:
    test_registry_persists_multiple_robots_and_selection()
    test_ip_change_updates_same_identity_without_duplicate()
    test_discovery_merge_retains_offline_robots()
    test_duplicate_discovery_packets_collapse_by_device_id()
    test_corrupt_registry_fails_safe_and_recovers_on_save()
    test_identity_serialization_roundtrip()
    test_first_flash_never_binds_arbitrary_existing_robot()
    test_ui_and_runtime_contract_source()
    print("EPIC H30 Multi-Robot Management: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
