#pragma once

#include <stdint.h>

#include "IResetReasonSource.h"

enum class ResetReason : uint8_t {
    POWER_ON = 0,
    SOFTWARE_RESET,
    WATCHDOG,
    BROWNOUT,
    PANIC,
    DEEP_SLEEP,
    UNKNOWN
};

class ResetReasonService {
public:
    explicit ResetReasonService(IResetReasonSource& source) : _source(source) {}

    void capture();

    bool captured() const { return _captured; }
    ResetReason reason() const { return _reason; }
    const char* name() const { return nameOf(_reason); }

    static ResetReason normalize(PlatformResetReason reason);
    static const char* nameOf(ResetReason reason);
    static bool isWatchdog(ResetReason reason) {
        return reason == ResetReason::WATCHDOG;
    }

private:
    IResetReasonSource& _source;
    bool _captured = false;
    ResetReason _reason = ResetReason::UNKNOWN;
};
