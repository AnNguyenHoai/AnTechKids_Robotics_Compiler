#pragma once

// Compatibility adapter for the Arduino-ESP32 2.x LEDC API used by the
// current PlatformIO environment. RobotAPI.cpp uses GPIO pins as the logical
// LEDC handle; this adapter preserves that call-site contract while mapping
// those pins to stable LEDC channels.

#include <Arduino.h>
#include <esp32-hal-ledc.h>

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR < 3

static inline uint8_t robotLedcChannelForPin(uint8_t pin)
{
    switch (pin)
    {
        case 25: return 0;
        case 26: return 1;
        case 27: return 2;
        case 14: return 3;
        default: return 0;
    }
}

static inline void robotLedcAttachCompat(uint8_t pin, uint32_t frequency, uint8_t resolution)
{
    const uint8_t channel = robotLedcChannelForPin(pin);
    ledcSetup(channel, frequency, resolution);
    ledcAttachPin(pin, channel);
}

static inline void robotLedcWriteCompat(uint8_t pin, uint32_t duty)
{
    ledcWrite(robotLedcChannelForPin(pin), duty);
}

#define ledcAttach(pin, frequency, resolution) \
    robotLedcAttachCompat((pin), (frequency), (resolution))
#define ledcWrite(pin, duty) \
    robotLedcWriteCompat((pin), (duty))

#endif
