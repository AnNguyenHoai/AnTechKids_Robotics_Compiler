from domain.hardware_config import HardwareConfig
from domain.hardware_requirement_validator import HardwareRequirementValidator


def configured(**states):
    config = HardwareConfig.create_default()
    for device_id, enabled in states.items():
        config.set_enabled(device_id, enabled)
    return config


def test_line_follow_requires_motor_and_line_sensor():
    config = configured(motor=True, line_sensor=False)
    result = HardwareRequirementValidator.validate(
        "import rcu\nrcu.line_follow(60)\n", config
    )
    assert not result.valid
    assert result.issues[0].disabled_devices == ("line_sensor",)


def test_line_follow_legacy_alias_is_detected():
    config = configured(motor=False, line_sensor=False)
    result = HardwareRequirementValidator.validate(
        "import rcu\nrcu.LineBasis(60)\n", config
    )
    assert not result.valid
    assert set(result.issues[0].disabled_devices) == {"line_sensor", "motor"}


def test_ultrasonic_requires_ultrasonic():
    config = configured(ultrasonic=False)
    result = HardwareRequirementValidator.validate(
        "import rcu\nd = rcu.GetUltrasound(1)\n", config
    )
    assert not result.valid
    assert result.issues[0].disabled_devices == ("ultrasonic",)


def test_enabled_hardware_passes():
    config = configured(motor=True, line_sensor=True, ultrasonic=True)
    source = """import rcu
rcu.line_follow(60)
rcu.GetUltrasound(1)
"""
    assert HardwareRequirementValidator.validate(source, config).valid


def test_syntax_error_is_left_to_language_compiler():
    config = configured(motor=False)
    assert HardwareRequirementValidator.validate("def :", config).valid
