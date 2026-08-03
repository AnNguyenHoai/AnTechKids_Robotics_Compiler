#ifndef DIAGNOSTICS_MANAGER_H
#define DIAGNOSTICS_MANAGER_H

#include <array>
#include "../Sensor/SensorID.h"          // sửa đường dẫn
#include "SensorStatistics.h"
#include "RollingBuffer.h"

constexpr size_t STABILITY_WINDOW = 100;

class DiagnosticsManager {
public:
    static DiagnosticsManager& instance();

    void updateSensors();
    void recordLoopTime(uint32_t us);
    void printReport();

    const SensorStatistics& getStatistics(SensorID id) const;

    uint32_t getTickCount() const { return tickCount; }
    float getLoopFrequency() const;

    uint32_t getLastLoopTimeUs() const { return lastLoopTimeUs; }
    uint32_t getMinLoopTimeUs() const { return minLoopTimeUs; }
    uint32_t getMaxLoopTimeUs() const { return maxLoopTimeUs; }

private:
    DiagnosticsManager() = default;
    DiagnosticsManager(const DiagnosticsManager&) = delete;
    DiagnosticsManager& operator=(const DiagnosticsManager&) = delete;

    std::array<SensorStatistics, static_cast<size_t>(SensorID::Count)> stats;
    std::array<RollingBuffer<STABILITY_WINDOW>, static_cast<size_t>(SensorID::Count)> buffers;

    uint32_t tickCount = 0;
    uint32_t totalLoopTimeUs = 0;
    uint32_t minLoopTimeUs = 0xFFFFFFFF;
    uint32_t maxLoopTimeUs = 0;
    uint32_t lastLoopTimeUs = 0;

    void updateSensor(SensorID id);
};

#endif