#pragma once

#include <stdint.h>

/**
 * H26-D canonical Robot VM error contract, schema version 1.
 * Numeric values are ABI-stable. Do not renumber existing codes.
 */
enum class VMErrorCode : uint8_t
{
    None            = 0,
    InvalidOpcode   = 1,
    ProgramOverflow = 2,
    InvalidJump     = 3,
    StackOverflow   = 4,
    InvalidReturn   = 5,
    DivisionByZero  = 6,
    ModuloByZero    = 7,
    InvalidOperand  = 8,
    InvalidVariable = 9,
    Unknown         = 0xFF
};

constexpr uint8_t VM_ERROR_CONTRACT_VERSION = 1;

constexpr uint8_t ToErrorCode(VMErrorCode error)
{
    return static_cast<uint8_t>(error);
}

constexpr bool IsKnownVMErrorCode(uint8_t code)
{
    return code <= ToErrorCode(VMErrorCode::InvalidVariable);
}

constexpr const char* VMErrorId(VMErrorCode error)
{
    switch (error)
    {
        case VMErrorCode::None:            return "ok";
        case VMErrorCode::InvalidOpcode:   return "invalid_opcode";
        case VMErrorCode::ProgramOverflow: return "program_overflow";
        case VMErrorCode::InvalidJump:     return "invalid_jump";
        case VMErrorCode::StackOverflow:   return "stack_overflow";
        case VMErrorCode::InvalidReturn:   return "invalid_return";
        case VMErrorCode::DivisionByZero:  return "division_by_zero";
        case VMErrorCode::ModuloByZero:    return "modulo_by_zero";
        case VMErrorCode::InvalidOperand:  return "invalid_operand";
        case VMErrorCode::InvalidVariable: return "invalid_variable";
        default:                           return "unknown";
    }
}

constexpr const char* VMErrorMessage(VMErrorCode error)
{
    switch (error)
    {
        case VMErrorCode::None:
            return "No VM error.";
        case VMErrorCode::InvalidOpcode:
            return "The program contains an opcode the VM cannot execute.";
        case VMErrorCode::ProgramOverflow:
            return "The program exceeds the VM instruction capacity.";
        case VMErrorCode::InvalidJump:
            return "A control-flow instruction targets an invalid program address.";
        case VMErrorCode::StackOverflow:
            return "The VM call stack is full.";
        case VMErrorCode::InvalidReturn:
            return "A return instruction was executed without an active call frame.";
        case VMErrorCode::DivisionByZero:
            return "The VM attempted integer division by zero.";
        case VMErrorCode::ModuloByZero:
            return "The VM attempted integer modulo by zero.";
        case VMErrorCode::InvalidOperand:
            return "An instruction references an operand outside the supported VM contract.";
        case VMErrorCode::InvalidVariable:
            return "An instruction references a variable outside the VM variable range.";
        default:
            return "Unknown VM error code.";
    }
}
