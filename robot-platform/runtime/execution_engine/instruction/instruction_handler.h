#pragma once

#include "instruction_context.h"
#include "execution_result.h"
#include "execution_types.h"
#include <string>
#include <cstdint>

namespace robot {
namespace execution {

class InstructionHandler {
public:
    virtual ~InstructionHandler() = default;

    virtual ExecutionResult execute(InstructionContext& ctx) = 0;
    virtual bool validate(InstructionContext& ctx) = 0;
    virtual std::string name() const = 0;
    virtual uint32_t opcode() const = 0;
    virtual InstructionCategory category() const = 0;
    virtual Semantic semantic() const = 0;
};

} // namespace execution
} // namespace robot