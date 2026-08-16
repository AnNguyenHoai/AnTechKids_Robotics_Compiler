#pragma once

#include "../instruction_handler.h"
#include "execution_types.h"
#include <string>

namespace robot {
namespace execution {
namespace control {

class JumpIfTrueInstruction : public InstructionHandler {
public:
    JumpIfTrueInstruction();

    ExecutionResult execute(InstructionContext& ctx) override;
    bool validate(InstructionContext& ctx) override;
    std::string name() const override;
    uint32_t opcode() const override;
    InstructionCategory category() const override;
    Semantic semantic() const override;

private:
    uint32_t m_opcode;
};

} // namespace control
} // namespace execution
} // namespace robot