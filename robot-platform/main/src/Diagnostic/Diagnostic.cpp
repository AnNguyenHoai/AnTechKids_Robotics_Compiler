#include "Diagnostic.h"
#include "../HardwareAbstraction/GPIO.h"
#include "../Health/BatteryMonitorPlatform.h"

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
    auto& battery = systemBatteryMonitor();
    if (!battery.sample()) {
        Serial.printf(
            "[DIAG] Battery: state=%s raw=%d calibration=PENDING_HW\n",
            BatteryMonitor::stateName(battery.state()),
            battery.lastRawAverage()
        );
        return;
    }

    Serial.printf(
        "[DIAG] Battery: voltage=%.2fV state=%s raw=%d\n",
        battery.voltage(),
        BatteryMonitor::stateName(battery.state()),
        battery.lastRawAverage()
    );
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