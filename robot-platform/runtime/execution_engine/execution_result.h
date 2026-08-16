#pragma once

#include "execution_types.h"
#include <string>
#include <cstdint>
#include <chrono>

namespace robot {
namespace execution {

struct ExecutionResult {
    ExecutionStatus status;
    uint32_t errorCode;
    std::string diagnosticMessage;
    uint32_t programCounter;
    ExecutionLayer layer;
    uint32_t opcodeId;
    std::chrono::microseconds executionTime;

    ExecutionResult(
        ExecutionStatus status = ExecutionStatus::Success,
        uint32_t errorCode = 0,
        const std::string& diagnosticMessage = "",
        uint32_t programCounter = 0,
        ExecutionLayer layer = ExecutionLayer::Unknown,
        uint32_t opcodeId = 0,
        std::chrono::microseconds executionTime = std::chrono::microseconds(0)
    ) : status(status), errorCode(errorCode), diagnosticMessage(diagnosticMessage),
        programCounter(programCounter), layer(layer), opcodeId(opcodeId),
        executionTime(executionTime) {}

    bool isSuccess() const { return status == ExecutionStatus::Success; }
    bool isFailure() const { return status == ExecutionStatus::Failure; }
    bool isError() const { return status == ExecutionStatus::Error; }
};

} // namespace execution
} // namespace robot