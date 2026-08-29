#pragma once

#include "../instruction_handler.h"
#include "execution_types.h"
#include <string>

namespace robot {
namespace execution {
namespace motion {

class SpeedInstruction : public InstructionHandler {
public:
    SpeedInstruction();

    ExecutionResult execute(InstructionContext& ctx) override;
    bool validate(InstructionContext& ctx) override;
    std::string name() const override;
    uint32_t opcode() const override;
    InstructionCategory category() const override;
    Semantic semantic() const override;

private:
    uint32_t m_opcode;
};

} // namespace motion
} // namespace execution
} // namespace robot