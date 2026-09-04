#include "instruction_dispatcher.h"
#include <chrono>

namespace robot {
namespace execution {

InstructionDispatcher::InstructionDispatcher(std::unique_ptr<InstructionFactory> factory)
    : m_factory(factory ? std::move(factory) : InstructionFactory::defaultFactory()),
      m_registry(nullptr) {}

void InstructionDispatcher::setFactory(std::unique_ptr<InstructionFactory> factory) {
    m_factory = std::move(factory);
}

void InstructionDispatcher::setRegistry(const InstructionRegistry& registry) {
    m_registry = &registry;
}

ExecutionResult InstructionDispatcher::dispatch(InstructionContext& ctx, uint32_t opcode) {
    auto start = std::chrono::steady_clock::now();

    // 1. Lookup metadata
    if (m_registry) {
        auto metaOpt = m_registry->lookup(opcode);
        if (!metaOpt.has_value()) {
            // Unknown opcode
            auto handler = m_factory->createHandler(opcode);
            auto result = handler->execute(ctx);
            result.executionTime = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::steady_clock::now() - start);
            result.opcodeId = opcode;
            result.layer = ExecutionLayer::Dispatcher;
            return result;
        }
        // Metadata found; could be used for validation later
        // For now, we still create handler via factory
    }

    // 2. Create handler via factory
    auto handler = m_factory->createHandler(opcode);

    // 3. Validate
    if (!handler->validate(ctx)) {
        return ExecutionResult(
            ExecutionStatus::Failure,
            2,
            "Instruction validation failed",
            ctx.context().programCounter().current(),
            ExecutionLayer::Dispatcher,
            opcode,
            std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - start)
        );
    }

    // 4. Execute
    auto result = handler->execute(ctx);
    result.executionTime = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now() - start);
    result.opcodeId = opcode;
    result.layer = ExecutionLayer::Dispatcher;
    if (result.programCounter == 0) {
        result.programCounter = ctx.context().programCounter().current();
    }
    return result;
}

} // namespace execution
} // namespace robot