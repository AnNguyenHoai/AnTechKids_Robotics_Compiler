from domain.hardware_config import HardwareConfig
from domain.program_capabilities import ProgramCapabilityAnalyzer


def configured(**states):
    config = HardwareConfig.create_default()
    for device_id, enabled in states.items():
        config.set_enabled(device_id, enabled)
    return config


def test_analyzer_collects_union_of_program_hardware_requirements():
    result = ProgramCapabilityAnalyzer.analyze(
        "import rcu\nrcu.forward(50)\nd = rcu.GetUltrasound(1)\n"
    )
    assert result.required_devices == ("motor", "ultrasonic")
    assert result.api_names == ("GetUltrasound", "forward")


def test_analyzer_detects_missing_capability_without_compiling():
    result = ProgramCapabilityAnalyzer.analyze("import rcu\nrcu.line_follow(60)\n")
    config = configured(motor=True, line_sensor=False)
    assert result.missing_devices(config) == ("line_sensor",)


def test_analyzer_accepts_legacy_module_alias():
    result = ProgramCapabilityAnalyzer.analyze(
        "import rcu as robot\nrobot.SetMp3Play(1)\n"
    )
    assert result.required_devices == ("buzzer",)


def test_analyzer_does_not_claim_unknown_or_non_hardware_apis():
    result = ProgramCapabilityAnalyzer.analyze(
        "import rcu\nrcu.SetWaitForTime(0.1)\nrcu.unknown_feature()\n"
    )
    assert result.required_devices == ()
    assert result.api_names == ()


def test_analyzer_treats_incomplete_python_as_unknown():
    result = ProgramCapabilityAnalyzer.analyze("import rcu\nrcu.line_follow(\n")
    assert result.syntax_error is True


def test_main_window_exposes_capability_status_controls():
    pytest = __import__("pytest")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from ui.main_window import Ui_MainWindow

    app = QApplication.instance() or QApplication([])
    from PySide6.QtWidgets import QMainWindow
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    assert ui.capability_group.title() == "Hardware Capability"
    assert ui.capability_summary is not None
    assert ui.capability_details is not None

    window.close()
