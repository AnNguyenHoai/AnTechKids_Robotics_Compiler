#include "RobotAPI.h"
#include "../../../include/generated/generated_device_config.h"
#include <Arduino.h>

namespace RobotAPI {

namespace {
constexpr uint32_t kMp3PlayDurationMs = 200;
}

uint32_t BeginMp3PlayCooperative(int index)
{
#if !ROBOT_FEATURE_BUZZER
    (void)index;
    return 0;
#else
    Serial.printf("[BUZZER] BeginMp3PlayCooperative index=%d duration=%lums\n",
                  index,
                  static_cast<unsigned long>(kMp3PlayDurationMs));
    digitalWrite(OUTPUT_BUZZER_PIN, HIGH);
    return kMp3PlayDurationMs;
#endif
}

void EndMp3PlayCooperative()
{
#if ROBOT_FEATURE_BUZZER
    digitalWrite(OUTPUT_BUZZER_PIN, LOW);
#endif
}

} // namespace RobotAPI
