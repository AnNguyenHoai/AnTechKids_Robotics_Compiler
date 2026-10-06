#pragma once
#include "TCRT5000.h"
#include "../Services/Line/LineSensorBank.h"

class MCPLineSensor : public TCRT5000 {
public:
    MCPLineSensor(LineSensorBank& bank, int channel, const char* sensorName)
        : TCRT5000(-1, sensorName, HIGH), _bank(bank), _channel(channel), _sensorName(sensorName) {}

    bool initialize() override;
    void update() override;
    bool healthy() const override;
    const char* name() const override;

private:
    LineSensorBank& _bank;
    int _channel;
    const char* _sensorName;
};
