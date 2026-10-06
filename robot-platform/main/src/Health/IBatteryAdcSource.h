#pragma once

#include <stdint.h>

class IBatteryAdcSource {
public:
    virtual ~IBatteryAdcSource() = default;
    virtual int readRaw() = 0;
};
