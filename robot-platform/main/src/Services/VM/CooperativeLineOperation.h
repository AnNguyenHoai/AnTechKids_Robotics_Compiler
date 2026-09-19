#pragma once

#include <stdint.h>

/**
 * H29 Runtime Cooperative Execution
 *
 * Long-running line operations are represented as small state machines. Each
 * Update() call performs at most one bounded control tick and then returns so
 * the top-level Arduino loop can continue servicing Wi-Fi, HTTP, OTA and UDP
 * discovery.
 */
namespace CooperativeLineOperation {

enum class Kind : uint8_t {
    None = 0,
    Millisecond,
    IntersectionStop,
    TurnEncounterLine,
    Bmp,
};

bool StartMillisecond(int speed, int milliseconds);
bool StartIntersectionStop(int speed, int type);
bool StartTurnEncounterLine(int speed, int angle, int direction);
bool StartBmp(int speed, int degree);

/** Advance one bounded control tick. Returns true while still pending. */
bool Update();

bool IsActive();
Kind CurrentKind();

/**
 * Cancel the active operation. When stopMotion is true, motors are stopped;
 * otherwise only the line state machine is cleared.
 */
void Cancel(bool stopMotion = true);

} // namespace CooperativeLineOperation
