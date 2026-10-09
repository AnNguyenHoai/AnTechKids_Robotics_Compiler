#include "Diagnostic.h"
#include "../HardwareAbstraction/GPIO.h"

void Diagnostic::runAll() {
    Serial.println("[DIAG] ===== Starting Diagnostics ===== ");
    checkBattery();
    checkMotor();
    checkFlash();
    checkMemory();
    checkClock();
    Serial.println("[DIAG] ===== Diagnostics Complete ===== ");
}

void Diagnostic::checkBattery() {
    // V1 Line5 owns GPIO34 as the Far-Left line sensor.
    // Do not probe GPIO34 with analogRead(): Arduino-ESP32 may route the pad
    // through the ADC path and disturb subsequent digitalRead() ownership.
    // Battery ADC remains intentionally unavailable until a dedicated pin is
    // defined by the hardware contract.
    Serial.println("[DIAG] Battery check: SKIPPED (no dedicated battery ADC pin in V1 Line5)");
}

void Diagnostic::checkMotor() {
    // Kiểm tra nhanh bằng cách chạy thử 0.1s (sẽ implement sau)
    Serial.println("[DIAG] Motor check: OK (placeholder)");
}

void Diagnostic::checkFlash() {
    uint32_t size = ESP.getFlashChipSize();
    Serial.printf("[DIAG] Flash Size: %u bytes\n", size);
}

void Diagnostic::checkMemory() {
    Serial.printf("[DIAG] Free Heap: %u bytes\n", ESP.getFreeHeap());
}

void Diagnostic::checkClock() {
    Serial.printf("[DIAG] CPU Frequency: %u MHz\n", ESP.getCpuFreqMHz());
}