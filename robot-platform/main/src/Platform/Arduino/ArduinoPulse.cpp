#include "../../HAL/PulseHal.h"
#include "../../HAL/GPIOHal.h"
#include <Arduino.h>

namespace HAL {

class ArduinoPulse : public PulseHal {
public:
    ArduinoPulse() = default;
    ~ArduinoPulse() = default;

    uint32_t pulseIn(uint32_t pin, PinState state, uint32_t timeoutUs) override {
        int level = (state == PinState::HIGH_STATE) ? HIGH : LOW;
        return ::pulseIn(pin, level, timeoutUs);
    }
};

PulseHal& getPulse() {
    static ArduinoPulse instance;
    return instance;
}

} // namespace HAL