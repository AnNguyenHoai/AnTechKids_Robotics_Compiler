#pragma once

#include "instruction_handler.h"
#include "instruction_factory.h"
#include "instruction_registry.h"
#include "instruction_context.h"
#include "execution_result.h"
#include <memory>
#include <cstdint>

namespace robot {
namespace execution {

class InstructionDispatcher {
public:
    InstructionDispatcher(std::unique_ptr<InstructionFactory> factory = nullptr);

    void setFactory(std::unique_ptr<InstructionFactory> factory);
    void setRegistry(const InstructionRegistry& registry);

    ExecutionResult dispatch(InstructionContext& ctx, uint32_t opcode);

private:
    std::unique_ptr<InstructionFactory> m_factory;
    const InstructionRegistry* m_registry;
};

} // namespace execution
} // namespace robot