#ifndef HAL_TIMEHAL_H
#define HAL_TIMEHAL_H

#include <stdint.h>

namespace HAL {

class TimeHal {
public:
    virtual ~TimeHal() = default;
    virtual void delayMs(uint32_t ms) = 0;
    virtual void delayUs(uint32_t us) = 0;
    virtual uint32_t millis() = 0;
    virtual uint32_t micros() = 0;
};

TimeHal& getTime();

} // namespace HAL

#endif