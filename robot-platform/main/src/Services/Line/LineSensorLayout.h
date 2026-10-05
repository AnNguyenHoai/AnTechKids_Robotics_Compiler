#ifndef LINE_SENSOR_LAYOUT_H
#define LINE_SENSOR_LAYOUT_H

#include <stdint.h>
#include "../../Sensor/SensorID.h"

namespace LineSensorLayout {

constexpr uint8_t MASK_FAR_LEFT  = 0x10;
constexpr uint8_t MASK_LEFT      = 0x08;
constexpr uint8_t MASK_CENTER    = 0x04;
constexpr uint8_t MASK_RIGHT     = 0x02;
constexpr uint8_t MASK_FAR_RIGHT = 0x01;
constexpr uint8_t MASK_ALL       = 0x1F;
constexpr uint8_t MASK_CENTER_ZONE = MASK_LEFT | MASK_CENTER | MASK_RIGHT;
constexpr int CHANNEL_COUNT = 5;

inline bool sensorIdFromChannel(int channel, SensorID& id) {
    // Preserve the public V1 channel contract for existing lessons:
    // 0=Left, 1=Center, 2=Right. New channels are appended.
    switch (channel) {
        case 0: id = SensorID::LineLeft; return true;
        case 1: id = SensorID::LineCenter; return true;
        case 2: id = SensorID::LineRight; return true;
        case 3: id = SensorID::LineFarLeft; return true;
        case 4: id = SensorID::LineFarRight; return true;
        default: return false;
    }
}

inline uint8_t sanitizeMask(uint8_t mask) {
    return static_cast<uint8_t>(mask & MASK_ALL);
}

inline bool isIntersectionCandidate(uint8_t mask) {
    mask = sanitizeMask(mask);
    uint8_t count = 0;
    while (mask != 0) {
        count += static_cast<uint8_t>(mask & 0x01u);
        mask >>= 1;
    }
    return count >= 4;
}

} // namespace LineSensorLayout

#endif // LINE_SENSOR_LAYOUT_H
