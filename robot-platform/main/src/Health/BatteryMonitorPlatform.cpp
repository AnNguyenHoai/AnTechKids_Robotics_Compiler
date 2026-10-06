#include "BatteryMonitorPlatform.h"

#include "ArduinoBatteryAdcSource.h"

BatteryMonitor& systemBatteryMonitor() {
    static ArduinoBatteryAdcSource source;

    // V2-HLT-001 fail-safe production default:
    // hardware docs identify a 7.5 V pack but do not yet define the V2 ADC
    // divider ratio or approved LOW/CRITICAL thresholds. Keep calibration
    // invalid until board measurements provide those values.
    static BatteryMonitorConfig config;
    static BatteryMonitor monitor(source, config);
    return monitor;
}
