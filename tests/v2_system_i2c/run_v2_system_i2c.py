from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANAGER_H = ROOT / "robot-platform/main/src/HardwareAbstraction/SystemI2CBusManager.h"
MANAGER_CPP = ROOT / "robot-platform/main/src/HardwareAbstraction/SystemI2CBusManager.cpp"
BOARD_PROFILE = ROOT / "robot-platform/main/src/HardwareAbstraction/BoardProfile.h"
ROBOT_API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
MPU_CPP = ROOT / "robot-platform/main/src/Drivers/MPU6050/MPU6050.cpp"
PLATFORM_SRC = ROOT / "robot-platform/main"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"Missing {label}: {needle}"


def test_fixed_bus_contract() -> None:
    profile = BOARD_PROFILE.read_text(encoding="utf-8")
    require(profile, "SYSTEM_I2C_SCL = 13", "System I2C SCL")
    require(profile, "SYSTEM_I2C_SDA = 21", "System I2C SDA")
    require(profile, "INITIAL_FREQUENCY_HZ = 400000", "400 kHz initial frequency")


def test_single_wire_begin_owner() -> None:
    owners = []
    for path in PLATFORM_SRC.rglob("*"):
        if path.suffix not in {".cpp", ".h", ".ino"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Wire.begin(" in text:
            owners.append(path.relative_to(ROOT).as_posix())

    assert owners == [
        "robot-platform/main/src/HardwareAbstraction/SystemI2CBusManager.cpp"
    ], f"Wire.begin ownership violation: {owners}"


def test_manager_is_idempotent_and_bounded() -> None:
    header = MANAGER_H.read_text(encoding="utf-8")
    impl = MANAGER_CPP.read_text(encoding="utf-8")

    require(header, "_beginAttempted", "one-attempt state")
    require(header, "_initialized", "initialized state")
    require(impl, "if (_beginAttempted)", "idempotent begin guard")
    require(impl, "_beginAttempted = true", "begin-attempt latch")
    require(impl, "Wire.begin(", "single physical bus init")
    require(impl, "SYSTEM_I2C_TIMEOUT_MS = 20", "bounded transaction timeout")
    require(impl, "Wire.setTimeOut(SYSTEM_I2C_TIMEOUT_MS)", "Wire timeout configuration")
    assert "while (" not in impl and "while(" not in impl, "System I2C init must not block in a retry loop"


def test_platform_initializes_bus_before_sensors() -> None:
    robot = ROBOT_API.read_text(encoding="utf-8")
    begin_pos = robot.index("SystemI2CBusManager::instance().begin()")
    sensors_pos = robot.index("mgr.initializeAll()")
    assert begin_pos < sensors_pos, "System I2C must initialize before sensor initialization"


def test_mpu_uses_shared_bus_without_reinitializing() -> None:
    mpu = MPU_CPP.read_text(encoding="utf-8")
    require(mpu, "SystemI2CBusManager::instance().ensureInitialized()", "MPU shared-bus dependency")
    assert "Wire.begin(" not in mpu, "MPU6050 must not independently initialize Wire"
    require(mpu, "System I2C bus unavailable", "deterministic shared-bus failure diagnostic")


def main() -> int:
    test_fixed_bus_contract()
    print("PASS: fixed System I2C BoardProfile contract")
    test_single_wire_begin_owner()
    print("PASS: exactly one Wire.begin owner")
    test_manager_is_idempotent_and_bounded()
    print("PASS: idempotent non-blocking System I2C initialization")
    test_platform_initializes_bus_before_sensors()
    print("PASS: platform initializes shared bus before sensors")
    test_mpu_uses_shared_bus_without_reinitializing()
    print("PASS: MPU6050 consumes shared System I2C bus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
