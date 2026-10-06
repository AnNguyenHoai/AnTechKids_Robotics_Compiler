#include "ResetReasonService.h"

void ResetReasonService::capture() {
    if (_captured) {
        return;
    }

    _reason = normalize(_source.readResetReason());
    _captured = true;
}

ResetReason ResetReasonService::normalize(PlatformResetReason reason) {
    switch (reason) {
        case PlatformResetReason::POWER_ON:
            return ResetReason::POWER_ON;
        case PlatformResetReason::SOFTWARE:
            return ResetReason::SOFTWARE_RESET;
        case PlatformResetReason::WATCHDOG:
            return ResetReason::WATCHDOG;
        case PlatformResetReason::BROWNOUT:
            return ResetReason::BROWNOUT;
        case PlatformResetReason::PANIC:
            return ResetReason::PANIC;
        case PlatformResetReason::DEEP_SLEEP:
            return ResetReason::DEEP_SLEEP;
        case PlatformResetReason::OTHER:
        default:
            return ResetReason::UNKNOWN;
    }
}

const char* ResetReasonService::nameOf(ResetReason reason) {
    switch (reason) {
        case ResetReason::POWER_ON: return "POWER_ON";
        case ResetReason::SOFTWARE_RESET: return "SOFTWARE_RESET";
        case ResetReason::WATCHDOG: return "WATCHDOG";
        case ResetReason::BROWNOUT: return "BROWNOUT";
        case ResetReason::PANIC: return "PANIC";
        case ResetReason::DEEP_SLEEP: return "DEEP_SLEEP";
        case ResetReason::UNKNOWN:
        default: return "UNKNOWN";
    }
}
