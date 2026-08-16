#include "vm_statistics.h"

namespace robot {
namespace execution {

VMStatistics::VMStatistics()
    : m_instructionCount(0), m_errorCount(0),
      m_totalExecutionTime(0), m_isRunning(false) {}

void VMStatistics::reset() {
    m_instructionCount = 0;
    m_errorCount = 0;
    m_totalExecutionTime = std::chrono::microseconds(0);
    m_isRunning = false;
}

void VMStatistics::incrementInstructions() {
    m_instructionCount++;
}

uint64_t VMStatistics::instructionCount() const {
    return m_instructionCount;
}

void VMStatistics::startExecution() {
    if (!m_isRunning) {
        m_startTime = std::chrono::steady_clock::now();
        m_isRunning = true;
    }
}

void VMStatistics::stopExecution() {
    if (m_isRunning) {
        auto now = std::chrono::steady_clock::now();
        m_totalExecutionTime += std::chrono::duration_cast<std::chrono::microseconds>(now - m_startTime);
        m_isRunning = false;
    }
}

std::chrono::microseconds VMStatistics::executionTime() const {
    if (m_isRunning) {
        auto now = std::chrono::steady_clock::now();
        return m_totalExecutionTime +
               std::chrono::duration_cast<std::chrono::microseconds>(now - m_startTime);
    }
    return m_totalExecutionTime;
}

void VMStatistics::incrementErrors() {
    m_errorCount++;
}

uint64_t VMStatistics::errorCount() const {
    return m_errorCount;
}

void VMStatistics::clearCounters() {
    m_instructionCount = 0;
    m_errorCount = 0;
    // Keep execution time
}

} // namespace execution
} // namespace robot