#pragma once

#include "instruction_handler.h"

namespace robot {
namespace execution {

class UnknownInstructionHandler : public InstructionHandler {
public:
    explicit UnknownInstructionHandler(uint32_t opcode);

    ExecutionResult execute(InstructionContext& ctx) override;
    bool validate(InstructionContext& ctx) override;
    std::string name() const override;
    uint32_t opcode() const override;
    InstructionCategory category() const override;
    Semantic semantic() const override;

private:
    uint32_t m_opcode;
};

} // namespace execution
} // namespace robot