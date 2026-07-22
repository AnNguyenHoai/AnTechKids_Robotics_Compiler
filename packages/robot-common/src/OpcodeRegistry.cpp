#include "OpcodeRegistry.h"
#include <stdexcept>

OpcodeRegistry& OpcodeRegistry::instance() {
    static OpcodeRegistry reg;
    return reg;
}

OpcodeRegistry::OpcodeRegistry() {
    names[Opcode::MoveRun]        = "MOVE_RUN";
    operandCounts[Opcode::MoveRun] = 2;
    descriptions[Opcode::MoveRun] = "Start continuous movement";

    names[Opcode::MoveRunTime]    = "MOVE_RUN_TIME";
    operandCounts[Opcode::MoveRunTime] = 3;
    descriptions[Opcode::MoveRunTime] = "Move for a duration";

    names[Opcode::MoveStop]       = "MOVE_STOP";
    operandCounts[Opcode::MoveStop] = 0;
    descriptions[Opcode::MoveStop] = "Stop all motion";

    names[Opcode::Wait]           = "WAIT";
    operandCounts[Opcode::Wait] = 1;
    descriptions[Opcode::Wait] = "Wait milliseconds";

    names[Opcode::Servo]          = "SERVO";
    operandCounts[Opcode::Servo] = 2;
    descriptions[Opcode::Servo] = "Set servo angle";

    names[Opcode::ReadTrace]      = "READ_TRACE";
    operandCounts[Opcode::ReadTrace] = 2;
    descriptions[Opcode::ReadTrace] = "Read trace sensor";

    names[Opcode::Jump]           = "JUMP";
    operandCounts[Opcode::Jump] = 1;
    descriptions[Opcode::Jump] = "Unconditional jump";

    names[Opcode::JumpIf]         = "JUMP_IF";
    operandCounts[Opcode::JumpIf] = 2;
    descriptions[Opcode::JumpIf] = "Conditional jump";

    names[Opcode::Call]           = "CALL";
    operandCounts[Opcode::Call] = 1;
    descriptions[Opcode::Call] = "Call function";

    names[Opcode::Return]         = "RETURN";
    operandCounts[Opcode::Return] = 0;
    descriptions[Opcode::Return] = "Return from function";

    names[Opcode::ThreadStart]    = "THREAD_START";
    operandCounts[Opcode::ThreadStart] = 1;
    descriptions[Opcode::ThreadStart] = "Start new thread";

    names[Opcode::ThreadEnd]      = "THREAD_END";
    operandCounts[Opcode::ThreadEnd] = 0;
    descriptions[Opcode::ThreadEnd] = "End current thread";
}

std::string OpcodeRegistry::getName(Opcode op) const {
    auto it = names.find(op);
    if (it != names.end()) return it->second;
    throw std::runtime_error("Unknown opcode");
}

uint8_t OpcodeRegistry::getOperandCount(Opcode op) const {
    auto it = operandCounts.find(op);
    if (it != operandCounts.end()) return it->second;
    throw std::runtime_error("Unknown opcode");
}

std::string OpcodeRegistry::getDescription(Opcode op) const {
    auto it = descriptions.find(op);
    if (it != descriptions.end()) return it->second;
    throw std::runtime_error("Unknown opcode");
}