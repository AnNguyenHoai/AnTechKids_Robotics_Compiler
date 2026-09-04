/**
 * H25-I - Runtime Hardware Capability Contract.
 *
 * The generated_device_config.h remains the build-time source of truth.
 * This class is the firmware-facing runtime contract: every supported
 * hardware feature has one stable capability identifier and one query path.
 */
#pragma once

#include <stdint.h>

namespace HardwareCapability {

enum class Device : uint8_t {
    Motor = 0,
    Encoder,
    LineSensor,
    Ultrasonic,
    IMU,
    Servo,
    Buzzer,
    Count
};

enum class State : uint8_t {
    Disabled = 0,
    Enabled = 1
};

/** Return whether the requested hardware feature is enabled in this build. */
bool isEnabled(Device device);

/** Return the stable human-readable device name. */
const char* name(Device device);

/** Return the 7-bit capability mask (bit N corresponds to Device N). */
uint8_t mask();

/** Print the complete capability contract to Serial. */
void printStatus();

/**
 * Stable fallback contract for a disabled feature:
 * - actuators: caller must not drive hardware
 * - sensors: caller returns a neutral/unavailable value
 *
 * The actual public API return values are documented at their API boundary.
 */
} // namespace HardwareCapability
