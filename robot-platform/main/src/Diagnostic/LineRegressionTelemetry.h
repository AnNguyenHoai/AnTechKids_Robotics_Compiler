#pragma once

namespace LineRegressionTelemetry {

// Format and enqueue a LINE-REG record. Serial remains available as a bench
// fallback; UDP transport, when enabled, is deferred to Update() so control-
// critical sensor/follower code never performs Wi-Fi I/O.
void Emit(const char* format, ...);

// Flush at most one queued record through the qualification UDP transport.
// Call only from the firmware background phase.
void Update();

}  // namespace LineRegressionTelemetry
