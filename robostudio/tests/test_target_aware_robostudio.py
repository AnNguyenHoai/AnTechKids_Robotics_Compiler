from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ROBOSTUDIO = ROOT / "robostudio"
if str(ROBOSTUDIO) not in sys.path:
    sys.path.insert(0, str(ROBOSTUDIO))

from domain.program_capabilities import ProgramCapabilityAnalyzer
from domain.target_capability_view import TargetCapabilityService, required_capabilities


def test_target_registry_is_available_to_robostudio():
    service = TargetCapabilityService.load()
    assert service.target_ids() == ("robosim", "esp32", "arduino")
    assert service.describe("esp32")


def test_program_requirements_are_compared_with_selected_target():
    analysis = ProgramCapabilityAnalyzer.analyze(
        "import rcu\nrcu.forward(50)\nrcu.GetUltrasound(1)\n"
    )
    required = required_capabilities(analysis.api_names)
    assert required == ("motion.basic", "sensor.ultrasonic")

    service = TargetCapabilityService.load()
    assert service.evaluate("esp32", required).ready is True


def test_target_reports_missing_capability_before_build():
    analysis = ProgramCapabilityAnalyzer.analyze(
        "import rcu\nrcu.SetMoveRunAngle(90, 50)\n"
    )
    required = required_capabilities(analysis.api_names)
    service = TargetCapabilityService.load()
    view = service.evaluate("arduino", required)
    assert view.ready is False
    assert view.missing == ("motion.encoder_angle",)


def test_unknown_target_is_not_treated_as_ready():
    import pytest
    from domain.target_capability_view import TargetCapabilityViewError

    service = TargetCapabilityService.load()
    with pytest.raises(TargetCapabilityViewError):
        service.evaluate("not-a-target", ("runtime.control",))


def test_program_analysis_remains_hardware_compatible():
    analysis = ProgramCapabilityAnalyzer.analyze("import rcu\nrcu.line_follow(60)\n")
    assert analysis.required_devices == ("line_sensor", "motor")


def test_main_window_exposes_target_and_capability_controls():
    import pytest
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QMainWindow
    from ui.main_window import Ui_MainWindow

    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)

    assert ui.target_combo is not None
    assert ui.target_description is not None
    assert ui.target_capability_details is not None
    assert ui.capability_group.title() == "Hardware & Target Capability"
    window.close()
