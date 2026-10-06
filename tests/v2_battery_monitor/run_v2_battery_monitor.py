from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEALTH = ROOT / "robot-platform/main/src/Health"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
DIAG = ROOT / "robot-platform/main/src/Diagnostic/Diagnostic.cpp"
OLD_DIAG = ROOT / "robot-platform/main/src/Diagnostic/Diagnostic.cpp"

HARNESS = r"""
#include <cassert>
#include <cmath>
#include <cstdint>
#include <vector>
#include "BatteryMonitor.h"

struct FakeAdc : IBatteryAdcSource {
    std::vector<int> samples;
    size_t index = 0;

    FakeAdc(std::initializer_list<int> values) : samples(values) {}

    int readRaw() override {
        assert(index < samples.size());
        return samples[index++];
    }
};

static BatteryMonitorConfig cfg() {
    BatteryMonitorConfig c;
    c.adcMaxCount = 1000;
    c.adcReferenceVolts = 10.0f;
    c.calibrationFactor = 1.0f;
    c.lowThresholdVolts = 7.0f;
    c.criticalThresholdVolts = 6.0f;
    c.hysteresisVolts = 0.2f;
    c.sampleCount = 5;
    c.invalidLowRaw = 0;
    c.invalidHighRaw = 1000;
    c.calibrationValid = true;
    return c;
}

int main() {
    {
        FakeAdc adc{{800, 820, 780, 800, 800}};
        BatteryMonitor m(adc, cfg());
        assert(m.sample());
        assert(m.lastRawAverage() == 800);
        assert(std::fabs(m.voltage() - 8.0f) < 0.0001f);
        assert(m.state() == BatteryState::GOOD);
    }

    {
        FakeAdc adc{{690, 690, 690, 690, 690,
                     710, 710, 710, 710, 710,
                     721, 721, 721, 721, 721}};
        BatteryMonitor m(adc, cfg());
        assert(m.sample() && m.state() == BatteryState::LOW_VOLTAGE);
        // 7.10 V does not clear LOW because recovery threshold is 7.20 V.
        assert(m.sample() && m.state() == BatteryState::LOW_VOLTAGE);
        assert(m.sample() && m.state() == BatteryState::GOOD);
    }

    {
        FakeAdc adc{{590, 590, 590, 590, 590,
                     610, 610, 610, 610, 610,
                     621, 621, 621, 621, 621}};
        BatteryMonitor m(adc, cfg());
        assert(m.sample() && m.state() == BatteryState::CRITICAL);
        // 6.10 V stays CRITICAL until 6.20 V hysteresis is cleared.
        assert(m.sample() && m.state() == BatteryState::CRITICAL);
        assert(m.sample() && m.state() == BatteryState::LOW_VOLTAGE);
    }

    {
        FakeAdc adc{{0}};
        BatteryMonitor m(adc, cfg());
        assert(!m.sample());
        assert(m.state() == BatteryState::INVALID);
    }

    {
        FakeAdc adc{{1000}};
        BatteryMonitor m(adc, cfg());
        assert(!m.sample());
        assert(m.state() == BatteryState::INVALID);
    }

    {
        FakeAdc adc{{800,800,800,800,800}};
        BatteryMonitorConfig c = cfg();
        c.calibrationValid = false;
        BatteryMonitor m(adc, c);
        assert(!m.sample());
        assert(m.state() == BatteryState::INVALID);
        assert(m.voltage() == 0.0f);
    }

    {
        FakeAdc adc{{400,400,400,400,400}};
        BatteryMonitorConfig c = cfg();
        c.calibrationFactor = 2.0f;
        BatteryMonitor m(adc, c);
        assert(m.sample());
        assert(std::fabs(m.voltage() - 8.0f) < 0.0001f);
        assert(m.state() == BatteryState::GOOD);
    }

    assert(std::string(BatteryMonitor::stateName(BatteryState::GOOD)) == "GOOD");
    assert(std::string(BatteryMonitor::stateName(BatteryState::LOW_VOLTAGE)) == "LOW");
    assert(std::string(BatteryMonitor::stateName(BatteryState::CRITICAL)) == "CRITICAL");
    assert(std::string(BatteryMonitor::stateName(BatteryState::INVALID)) == "INVALID");

    return 0;
}
"""

def test_real_battery_monitor_cpp() -> None:
    harness = HARNESS.replace("#include <vector>", "#include <vector>\n#include <cstddef>\n#include <initializer_list>\n#include <string>")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src = td / "battery_monitor_test.cpp"
        exe = td / "battery_monitor_test"
        src.write_text(harness, encoding="utf-8")
        subprocess.run([
            "g++", "-std=c++11", "-Wall", "-Wextra", "-Werror",
            "-I", str(HEALTH),
            str(src), str(HEALTH / "BatteryMonitor.cpp"),
            "-o", str(exe),
        ], check=True)
        subprocess.run([str(exe)], check=True)


def test_gpio32_and_adc_ownership() -> None:
    profile = (HAL / "BoardProfile.h").read_text(encoding="utf-8")
    source = (HEALTH / "ArduinoBatteryAdcSource.cpp").read_text(encoding="utf-8")
    diag = DIAG.read_text(encoding="utf-8")

    assert "BATTERY_ADC = 32" in profile
    assert "BoardProfile::Pins::BATTERY_ADC" in source
    assert "HAL::getGPIO().analogRead" in source

    # Remove the obsolete GPIO34 battery diagnostic so encoder L-A is not sampled as ADC.
    assert "analogRead(34)" not in diag
    assert "* 2.0" not in diag
    assert "systemBatteryMonitor()" in diag


def test_production_default_is_fail_safe_until_calibrated() -> None:
    platform = (HEALTH / "BatteryMonitorPlatform.cpp").read_text(encoding="utf-8")
    header = (HEALTH / "BatteryMonitor.h").read_text(encoding="utf-8")
    assert "calibrationValid = false" in header
    assert "7.5 V pack" in platform
    assert "PENDING_HW" not in platform or "hardware" in platform
    assert "percentage" not in header.lower()


def main() -> int:
    test_real_battery_monitor_cpp()
    print("PASS: real BatteryMonitor C++ filtering/calibration/hysteresis/invalid regression")
    test_gpio32_and_adc_ownership()
    print("PASS: battery ADC ownership migrated from legacy GPIO34 to BoardProfile GPIO32")
    test_production_default_is_fail_safe_until_calibrated()
    print("PASS: production battery state remains INVALID until hardware calibration is approved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
