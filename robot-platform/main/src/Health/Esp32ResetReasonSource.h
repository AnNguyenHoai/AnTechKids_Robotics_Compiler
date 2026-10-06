#pragma once

#include "IResetReasonSource.h"

class Esp32ResetReasonSource : public IResetReasonSource {
public:
    PlatformResetReason readResetReason() override;
};
