from domain.device_registry import DeviceRegistry
from domain.hardware_build_matrix import HardwareBuildMatrix


def test_matrix_contains_on_and_off_case_for_every_registered_device():
    cases = HardwareBuildMatrix.cases()
    assert len(cases) == len(DeviceRegistry.ids()) * 2
    for device_id in DeviceRegistry.ids():
        states = {case.enabled for case in cases if case.device_id == device_id}
        assert states == {False, True}


def test_full_hardware_build_matrix_regression_passes():
    result = HardwareBuildMatrix.verify()
    assert result.passed, "\n".join(result.failures)
