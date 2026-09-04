#pragma once

#include <memory>
#include <cstdint>
#include "instruction_handler.h"

namespace robot {
namespace execution {

class InstructionFactory {
public:
    virtual ~InstructionFactory() = default;

    virtual std::unique_ptr<InstructionHandler> createHandler(uint32_t opcode) const;

    static std::unique_ptr<InstructionFactory> defaultFactory();
};

} // namespace execution
} // namespace robot