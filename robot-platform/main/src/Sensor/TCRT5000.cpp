#include "TCRT5000.h"
#include "LineSensorSnapshot.h"
#include "../HAL/HAL.h"
#include "../Diagnostic/LineRegressionTelemetry.h"
#include <Arduino.h>

#ifndef LINE_REGRESSION_DIAGNOSTICS
#define LINE_REGRESSION_DIAGNOSTICS 0
#endif

#ifndef LINE_REGRESSION_LEGACY_ACQUISITION
#define LINE_REGRESSION_LEGACY_ACQUISITION 0
#endif

TCRT5000::TCRT5000(int pin, const char* sensorName, int threshold)
    : _pin(pin), _name(sensorName), _threshold(threshold),
      _lastReading(0), _lastDiagnosticReading(-1), _healthy(true) {}

bool TCRT5000::initialize() {
    HAL::getGPIO().pinMode(_pin, HAL::PinMode::INPUT_MODE);
    _healthy = true;
    return true;
}

int TCRT5000::ReadHardwareLevelDirect() const {
    auto state = HAL::getGPIO().digitalRead(_pin);
    return (state == HAL::PinState::HIGH_STATE) ? 1 : 0;
}

void TCRT5000::SampleHardwareDirect() {
    _lastReading = ReadHardwareLevelDirect();
#if LINE_REGRESSION_DIAGNOSTICS
    // State-change logging avoids turning diagnostic transport into a control
    // timing bottleneck. The telemetry layer defers any UDP I/O to background.
    if (_lastReading != _lastDiagnosticReading) {
        LineRegressionTelemetry::Emit(
            "[LINE-REG][SENSOR] mode=%s name=%s raw=%d cache=%d detected=%d threshold=%d",
            LINE_REGRESSION_LEGACY_ACQUISITION ? "legacy" : "snapshot",
            _name,
            _lastReading,
            _lastReading,
            isLineDetected() ? 1 : 0,
            _threshold
        );
        _lastDiagnosticReading = _lastReading;
    }
#endif
}

void TCRT5000::ApplySnapshotReading(int reading) {
    _lastReading = reading ? 1 : 0;
}

bool TCRT5000::ReadHardwareDetectedDirect() const {
    return ReadHardwareLevelDirect() == _threshold;
}

void TCRT5000::update() {
#if LINE_REGRESSION_LEGACY_ACQUISITION
    // Qualification-only A/B path: restore the pre-snapshot behavior where
    // every consumer update performs an immediate physical GPIO acquisition.
    // Production builds leave this macro undefined/zero.
    SampleHardwareDirect();
    return;
#endif

    if (LineSensorSnapshot::IsCycleActive()) {
        LineSensorSnapshot::EnsureSample();
        LineSensorSnapshot::RecordConsumer();
        return;
    }
    SampleHardwareDirect();
}

bool TCRT5000::healthy() const {
    return _healthy;
}

const char* TCRT5000::name() const {
    return _name;
}

void TCRT5000::shutdown() {
    // Nothing to release
}

int TCRT5000::read() const {
    return _lastReading;
}

bool TCRT5000::isLineDetected() const {
    return (_lastReading == _threshold);
}

int TCRT5000::rawLevel() const {
    return _lastReading;
}

void TCRT5000::setThreshold(int threshold) {
    _threshold = threshold;
}

int TCRT5000::getThreshold() const {
    return _threshold;
}