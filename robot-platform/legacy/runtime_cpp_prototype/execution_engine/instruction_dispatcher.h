#pragma once

#include <cstdint>
#include <functional>
#include <unordered_map>
#include "execution_context.h"
#include "instruction_registry.h"
#include "execution_result.h"

namespace robot {
namespace execution {

class InstructionDispatcher {
public:
    using HandlerFunction = std::function<ExecutionResult(ExecutionContext&, uint32_t, const std::vector<int>&)>;

    InstructionDispatcher();

    void registerHandler(uint32_t opcode, HandlerFunction handler);
    ExecutionResult dispatch(ExecutionContext& context, uint32_t opcode, const std::vector<int>& operands = {});

    // Convenience to get registry
    InstructionRegistry& registry();

private:
    std::unordered_map<uint32_t, HandlerFunction> m_handlers;
    InstructionRegistry m_registry;
};

} // namespace execution
} // namespace robot