#ifndef HAL_PULSEHAL_H
#define HAL_PULSEHAL_H

#include <stdint.h>
#include "GPIOHal.h"

namespace HAL {

class PulseHal {
public:
    virtual ~PulseHal() = default;
    virtual uint32_t pulseIn(uint32_t pin, PinState state, uint32_t timeoutUs = 30000) = 0;
};

PulseHal& getPulse();

} // namespace HAL

#endif