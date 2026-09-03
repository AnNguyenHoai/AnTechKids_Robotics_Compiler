"""H25-G hardware ON/OFF build-matrix regression support."""
from dataclasses import dataclass
from typing import Dict, Tuple

from domain.device_registry import DeviceRegistry
from domain.hardware_config import HardwareConfig
from domain.hardware_macro_generator import HardwareMacroGenerator
from domain.hardware_requirement_validator import HardwareRequirementValidator


@dataclass(frozen=True)
class HardwareBuildCase:
    device_id: str
    enabled: bool
    expected_macro: int


@dataclass(frozen=True)
class HardwareBuildMatrixResult:
    passed: bool
    failures: Tuple[str, ...]


class HardwareBuildMatrix:
    """Runs deterministic ON/OFF regression checks for every registered device.

    This is intentionally independent of the local Arduino toolchain. It verifies
    the configuration -> macro contract and the RoboStudio program capability
    contract. Firmware compilation remains the responsibility of the firmware CI/
    Arduino environment, where all selected matrix headers can be compiled.
    """

    @classmethod
    def cases(cls) -> Tuple[HardwareBuildCase, ...]:
        cases = []
        for device_id in DeviceRegistry.ids():
            cases.append(HardwareBuildCase(device_id, False, 0))
            cases.append(HardwareBuildCase(device_id, True, 1))
        return tuple(cases)

    @classmethod
    def verify(cls) -> HardwareBuildMatrixResult:
        failures = []
        generator = HardwareMacroGenerator()
        for case in cls.cases():
            config = HardwareConfig.create_default()
            config.set_enabled(case.device_id, case.enabled)
            header = generator.render(config)
            macro = cls._macro_name(case.device_id)
            expected = f"#define {macro} {case.expected_macro}"
            expected_parts = ("#define", macro, str(case.expected_macro))
            if not any(line.split() == list(expected_parts) for line in header.splitlines()):
                failures.append(
                    f"{case.device_id}={'ON' if case.enabled else 'OFF'}: "
                    f"expected '{expected}'"
                )

        # Regression checks for program requirements in representative ON/OFF states.
        requirement_cases = (
            ("motion_on", "import rcu\nrcu.forward(50)\n", {"motor": True}, True),
            ("motion_off", "import rcu\nrcu.forward(50)\n", {"motor": False}, False),
            ("line_on", "import rcu\nrcu.line_follow(60)\n", {"motor": True, "line_sensor": True}, True),
            ("line_sensor_off", "import rcu\nrcu.line_follow(60)\n", {"motor": True, "line_sensor": False}, False),
            ("ultrasonic_off", "import rcu\nrcu.GetUltrasound(1)\n", {"ultrasonic": False}, False),
            ("servo_off", "import rcu\nrcu.SetServo(90)\n", {"servo": False}, False),
            ("buzzer_off", "import rcu\nrcu.SetMp3Play(1)\n", {"buzzer": False}, False),
        )
        for name, source, states, expected_valid in requirement_cases:
            config = HardwareConfig.create_default()
            for device_id, enabled in states.items():
                config.set_enabled(device_id, enabled)
            result = HardwareRequirementValidator.validate(source, config)
            if result.valid != expected_valid:
                failures.append(f"requirement case {name}: expected valid={expected_valid}, got {result.valid}")

        return HardwareBuildMatrixResult(not failures, tuple(failures))

    @staticmethod
    def _macro_name(device_id: str) -> str:
        return "ROBOT_FEATURE_" + device_id.upper()
