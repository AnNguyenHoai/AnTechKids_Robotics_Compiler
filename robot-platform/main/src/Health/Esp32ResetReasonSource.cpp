#include "Esp32ResetReasonSource.h"

#include <esp_system.h>

PlatformResetReason Esp32ResetReasonSource::readResetReason() {
    const esp_reset_reason_t reason = esp_reset_reason();

    switch (reason) {
        case ESP_RST_POWERON:
            return PlatformResetReason::POWER_ON;

        case ESP_RST_SW:
            return PlatformResetReason::SOFTWARE;

        case ESP_RST_INT_WDT:
        case ESP_RST_TASK_WDT:
        case ESP_RST_WDT:
            return PlatformResetReason::WATCHDOG;

        case ESP_RST_BROWNOUT:
            return PlatformResetReason::BROWNOUT;

        case ESP_RST_PANIC:
            return PlatformResetReason::PANIC;

        case ESP_RST_DEEPSLEEP:
            return PlatformResetReason::DEEP_SLEEP;

        default:
            return PlatformResetReason::OTHER;
    }
}
