#pragma once

#include <cstdint>
#include <chrono>

namespace robot {
namespace execution {

class VMStatistics {
public:
    VMStatistics();

    void reset();

    // Instruction counting
    void incrementInstructions();
    uint64_t instructionCount() const;

    // Execution time
    void startExecution();
    void stopExecution();
    std::chrono::microseconds executionTime() const;

    // Error tracking
    void incrementErrors();
    uint64_t errorCount() const;

    // Reset counters (keeps execution time)
    void clearCounters();

private:
    uint64_t m_instructionCount;
    uint64_t m_errorCount;
    std::chrono::steady_clock::time_point m_startTime;
    std::chrono::microseconds m_totalExecutionTime;
    bool m_isRunning;
};

} // namespace execution
} // namespace robot