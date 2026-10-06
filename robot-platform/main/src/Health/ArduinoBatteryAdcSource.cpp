#include "ArduinoBatteryAdcSource.h"

#include "../HAL/GPIOHal.h"
#include "../HardwareAbstraction/BoardProfile.h"

int ArduinoBatteryAdcSource::readRaw() {
    return HAL::getGPIO().analogRead(BoardProfile::Pins::BATTERY_ADC);
}
