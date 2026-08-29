from pathlib import Path

from domain.hardware_config import HardwareConfig
from domain.hardware_macro_generator import HardwareMacroGenerator
from domain.hardware_config_service import HardwareConfigService
from services.hardware_macro_service import HardwareMacroService


def test_render_contains_every_registered_device():
    config = HardwareConfig.create_default()
    config.set_enabled("imu", True)
    config.set_enabled("line_sensor", False)

    content = HardwareMacroGenerator().render(config)

    assert "#define ROBOT_FEATURE_MOTOR" in content
    assert "ROBOT_FEATURE_IMU" in content and content.rstrip().endswith("#define ROBOT_FEATURE_BUZZER             0")
    assert "ROBOT_FEATURE_IMU                1" in content
    assert "ROBOT_FEATURE_LINE_SENSOR        0" in content


def test_generate_writes_deterministic_header(tmp_path: Path):
    config = HardwareConfig.create_default()
    output = tmp_path / "generated_device_config.h"

    generator = HardwareMacroGenerator()
    generator.generate(config, output)

    assert output.exists()
    assert output.read_text(encoding="utf-8") == generator.render(config)


def test_macro_service_uses_persisted_hardware_json(tmp_path: Path):
    config_path = tmp_path / "hardware.json"
    output = tmp_path / "generated" / "generated_device_config.h"
    config_service = HardwareConfigService(config_path)
    config = HardwareConfig.create_default()
    config.set_enabled("encoder", True)
    config.set_enabled("imu", True)
    config_service.save(config)

    service = HardwareMacroService(config_service=config_service, output_path=output)
    result = service.generate()

    assert result == output
    content = output.read_text(encoding="utf-8")
    assert "ROBOT_FEATURE_ENCODER            1" in content
    assert "ROBOT_FEATURE_IMU                1" in content
