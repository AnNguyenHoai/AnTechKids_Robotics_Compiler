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
    // Giả sử dùng ADC trên chân GPIO34 (không có pull-up)
    analogRead(34); // Đọc trước để ổn định
    int raw = analogRead(34);
    // Giả sử cầu phân áp 2:1, Vref = 3.3V
    float voltage = (raw / 4095.0) * 3.3 * 2.0;
    Serial.printf("[DIAG] Battery Voltage: %.2f V\n", voltage);
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