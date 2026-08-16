#include "instruction_dispatcher.h"

namespace robot {
namespace execution {

InstructionDispatcher::InstructionDispatcher() {}

void InstructionDispatcher::registerHandler(uint32_t opcode, HandlerFunction handler) {
    m_handlers[opcode] = handler;
}

ExecutionResult InstructionDispatcher::dispatch(ExecutionContext& context, uint32_t opcode, const std::vector<int>& operands) {
    auto it = m_handlers.find(opcode);
    if (it != m_handlers.end()) {
        return it->second(context, opcode, operands);
    }
    return ExecutionResult(false, 1, "Opcode not implemented (stub)");
}

InstructionRegistry& InstructionDispatcher::registry() {
    return m_registry;
}

} // namespace execution
} // namespace robot