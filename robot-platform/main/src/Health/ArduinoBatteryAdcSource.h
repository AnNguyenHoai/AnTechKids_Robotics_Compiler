#pragma once

#include "IBatteryAdcSource.h"

class ArduinoBatteryAdcSource : public IBatteryAdcSource {
public:
    int readRaw() override;
};
