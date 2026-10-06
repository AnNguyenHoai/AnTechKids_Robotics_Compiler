from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "robot-platform/main/src/HardwareAbstraction/BoardProfile.h"
GPIO = ROOT / "robot-platform/main/src/HardwareAbstraction/GPIO.h"
HARDWARE_JSON = ROOT / "robostudio/config/hardware.json"
GENERATED_CONFIG = ROOT / "robot-platform/main/include/generated/generated_device_config.h"


def require(text: str, needle: str, label: str) -> None:
    assert needle in text, f"Missing {label}: {needle}"


def test_board_profile_contract() -> None:
    profile = PROFILE.read_text(encoding="utf-8")

    require(profile, 'ID = "antech_robot_v2"', "stable profile ID")
    require(profile, "MOTOR_SAFE_EN = 4", "motor safety pin")
    require(profile, "SYSTEM_I2C_SCL = 13", "I2C SCL")
    require(profile, "SYSTEM_I2C_SDA = 21", "I2C SDA")
    require(profile, "MOTOR_R_IN4 = 14", "motor right IN4")
    require(profile, "MOTOR_L_IN1 = 25", "motor left IN1")
    require(profile, "MOTOR_L_IN2 = 26", "motor left IN2")
    require(profile, "MOTOR_R_IN3 = 27", "motor right IN3")
    require(profile, "SERVO1 = 16", "servo 1")
    require(profile, "SERVO2 = 17", "servo 2")
    require(profile, "ULTRASONIC_ECHO = 22", "ultrasonic echo")
    require(profile, "ULTRASONIC_TRIG = 23", "ultrasonic trig")
    require(profile, "BATTERY_ADC = 32", "battery ADC")
    require(profile, "START_ARM = 33", "START/ARM")
    require(profile, "ENCODER_L_A = 34", "encoder left A")
    require(profile, "ENCODER_L_B = 35", "encoder left B")
    require(profile, "ENCODER_R_A = 36", "encoder right A")
    require(profile, "ENCODER_R_B = 39", "encoder right B")
    require(profile, "ADDRESS = 0x20", "MCP23017 address")


def test_gpio_facade_uses_board_profile() -> None:
    gpio = GPIO.read_text(encoding="utf-8")
    require(gpio, '#include "BoardProfile.h"', "BoardProfile include")

    aliases = (
        "MOTOR_SAFE_EN_PIN",
        "SYSTEM_I2C_SCL_PIN",
        "SYSTEM_I2C_SDA_PIN",
        "MOTOR_L_IN1_PIN",
        "MOTOR_L_IN2_PIN",
        "MOTOR_R_IN3_PIN",
        "MOTOR_R_IN4_PIN",
        "SERVO_1_PIN",
        "SERVO_2_PIN",
        "SONIC_ECHO_PIN",
        "SONIC_TRIG_PIN",
        "BATTERY_ADC_PIN",
        "START_ARM_PIN",
        "ENCODER_LEFT_A_PIN",
        "ENCODER_LEFT_B_PIN",
        "ENCODER_RIGHT_A_PIN",
        "ENCODER_RIGHT_B_PIN",
        "MCP23017_I2C_ADDRESS",
        "MPU6050_SDA_PIN",
        "MPU6050_SCL_PIN",
    )
    for alias in aliases:
        line = next((ln for ln in gpio.splitlines() if ln.startswith(f"#define {alias}")), None)
        assert line is not None, f"Missing compatibility alias {alias}"
        assert "BoardProfile::" in line, f"{alias} bypasses BoardProfile: {line}"

    assert "SENSOR_TRCT5000_" not in gpio, "V2-SW-004 must remove direct-GPIO Line5 aliases"
    for legacy in ("OUTPUT_LED_LEFT_PIN", "OUTPUT_LED_RIGHT_PIN", "OUTPUT_BUZZER_PIN"):
        assert legacy not in gpio, f"V2-SW-008 must remove direct-GPIO auxiliary alias: {legacy}"


def test_hardware_config_cannot_remap_wiring() -> None:
    config = json.loads(HARDWARE_JSON.read_text(encoding="utf-8"))
    assert set(config.keys()) == {"version", "devices"}, "HardwareConfig gained board wiring fields"
    assert isinstance(config["devices"], dict)
    assert all(isinstance(v, bool) for v in config["devices"].values())
    serialized = json.dumps(config).lower()
    for forbidden in ("gpio", "pin", "mcp23017", "address", "connector"):
        assert forbidden not in serialized, f"HardwareConfig must not own physical wiring: {forbidden}"

    generated = GENERATED_CONFIG.read_text(encoding="utf-8")
    assert "ROBOT_FEATURE_" in generated, "Generated config must retain feature enable/disable macros"
    for forbidden in ("GPIO", "_PIN", "MCP23017_I2C_ADDRESS"):
        assert forbidden not in generated, f"Generated feature config leaked physical wiring: {forbidden}"


def main() -> int:
    test_board_profile_contract()
    print("PASS: V2 BoardProfile fixed physical mapping")

    test_gpio_facade_uses_board_profile()
    print("PASS: GPIO compatibility facade delegates V2 wiring to BoardProfile")

    test_hardware_config_cannot_remap_wiring()
    print("PASS: HardwareConfig remains feature-state only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
