#include "../../HAL/TimeHal.h"
#include <Arduino.h>

namespace HAL {

class ArduinoTime : public TimeHal {
public:
    ArduinoTime() = default;
    ~ArduinoTime() = default;

    void delayMs(uint32_t ms) override { ::delay(ms); }
    void delayUs(uint32_t us) override { ::delayMicroseconds(us); }
    uint32_t millis() override { return ::millis(); }
    uint32_t micros() override { return ::micros(); }
};

TimeHal& getTime() {
    static ArduinoTime instance;
    return instance;
}

} // namespace HAL