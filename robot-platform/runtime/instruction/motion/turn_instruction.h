#pragma once

#include "../instruction_handler.h"
#include "motion_instruction_common.h"
#include "execution_types.h"
#include <string>

namespace robot {
namespace execution {
namespace motion {

class TurnInstruction : public InstructionHandler {
public:
    TurnInstruction();

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