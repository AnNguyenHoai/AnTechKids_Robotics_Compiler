#include "LocalHealthDisplayPlatform.h"

#include "NullLocalHealthDisplay.h"
#include "RobotHealthPlatform.h"

LocalHealthDisplayController& systemLocalHealthDisplay() {
    // V2-HLT-005 hardware contract is intentionally unresolved:
    // no OLED controller, I2C address, geometry, power contract, or driver
    // dependency is defined in the current V2 hardware source-of-truth.
    // Keep runtime integration optional/fail-open until that contract exists.
    static NullLocalHealthDisplay display;
    static LocalHealthDisplayController controller(systemRobotHealth(), display);
    return controller;
}
