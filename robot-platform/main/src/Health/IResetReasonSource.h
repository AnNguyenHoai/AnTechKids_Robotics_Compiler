#pragma once

#include <stdint.h>

enum class PlatformResetReason : uint8_t {
    POWER_ON = 0,
    SOFTWARE,
    WATCHDOG,
    BROWNOUT,
    PANIC,
    DEEP_SLEEP,
    OTHER
};

class IResetReasonSource {
public:
    virtual ~IResetReasonSource() = default;
    virtual PlatformResetReason readResetReason() = 0;
};
