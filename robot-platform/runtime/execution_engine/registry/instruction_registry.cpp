#include "instruction_registry.h"
#include "execution_types.h"

namespace robot {
namespace execution {

InstructionRegistry::InstructionRegistry() {
    // Core instructions (giữ nguyên)
    registerInstruction({static_cast<uint32_t>(Opcode::NOP), "NOP", InstructionCategory::Internal, Semantic::Native, 0, true, false, "No operation"});
    registerInstruction({static_cast<uint32_t>(Opcode::END), "END", InstructionCategory::Internal, Semantic::Native, 0, true, false, "Terminate execution"});
    registerInstruction({static_cast<uint32_t>(Opcode::WAIT), "WAIT", InstructionCategory::Internal, Semantic::Native, 1, true, false, "Wait (non-blocking stub)"});
    registerInstruction({static_cast<uint32_t>(Opcode::JUMP), "JUMP", InstructionCategory::Internal, Semantic::Native, 1, true, false, "Unconditional jump"});
    registerInstruction({static_cast<uint32_t>(Opcode::JUMP_IF), "JUMP_IF", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Conditional jump"});
    registerInstruction({static_cast<uint32_t>(Opcode::LOAD_CONST), "LOAD_CONST", InstructionCategory::Internal, Semantic::Native, 1, true, false, "Load constant onto stack"});
    registerInstruction({static_cast<uint32_t>(Opcode::STORE), "STORE", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Store value to variable"});
    registerInstruction({static_cast<uint32_t>(Opcode::LOAD), "LOAD", InstructionCategory::Internal, Semantic::Native, 1, true, false, "Load variable onto stack"});
    registerInstruction({static_cast<uint32_t>(Opcode::RETURN), "RETURN", InstructionCategory::Internal, Semantic::Native, 0, true, false, "Return from function"});

    // Motion instructions
    registerInstruction({static_cast<uint32_t>(Opcode::FORWARD), "FORWARD", InstructionCategory::Motion, Semantic::Native, 2, true, false, "Move forward"});
    registerInstruction({static_cast<uint32_t>(Opcode::BACKWARD), "BACKWARD", InstructionCategory::Motion, Semantic::Native, 2, true, false, "Move backward"});
    registerInstruction({static_cast<uint32_t>(Opcode::TURN_LEFT), "TURN_LEFT", InstructionCategory::Motion, Semantic::Native, 2, true, false, "Turn left"});
    registerInstruction({static_cast<uint32_t>(Opcode::TURN_RIGHT), "TURN_RIGHT", InstructionCategory::Motion, Semantic::Native, 2, true, false, "Turn right"});
    registerInstruction({static_cast<uint32_t>(Opcode::STOP), "STOP", InstructionCategory::Motion, Semantic::Native, 0, true, false, "Stop"});
    registerInstruction({static_cast<uint32_t>(Opcode::SET_SPEED), "SET_SPEED", InstructionCategory::Motion, Semantic::Native, 2, true, false, "Set motor speeds"});
    // Control instructions
    registerInstruction({static_cast<uint32_t>(Opcode::JUMP), "JUMP", InstructionCategory::Internal, Semantic::Native, 1, true, false, "Unconditional jump"});
    registerInstruction({static_cast<uint32_t>(Opcode::JUMP_IF_TRUE), "JUMP_IF_TRUE", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Jump if true"});
    registerInstruction({static_cast<uint32_t>(Opcode::JUMP_IF_FALSE), "JUMP_IF_FALSE", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Jump if false"});
    registerInstruction({static_cast<uint32_t>(Opcode::COMPARE_EQ), "COMPARE_EQ", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Compare equal"});
    registerInstruction({static_cast<uint32_t>(Opcode::COMPARE_NE), "COMPARE_NE", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Compare not equal"});
    registerInstruction({static_cast<uint32_t>(Opcode::COMPARE_LT), "COMPARE_LT", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Compare less than"});
    registerInstruction({static_cast<uint32_t>(Opcode::COMPARE_LE), "COMPARE_LE", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Compare less or equal"});
    registerInstruction({static_cast<uint32_t>(Opcode::COMPARE_GT), "COMPARE_GT", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Compare greater than"});
    registerInstruction({static_cast<uint32_t>(Opcode::COMPARE_GE), "COMPARE_GE", InstructionCategory::Internal, Semantic::Native, 2, true, false, "Compare greater or equal"});
    registerInstruction({static_cast<uint32_t>(Opcode::RETURN), "RETURN", InstructionCategory::Internal, Semantic::Native, 0, true, false, "Return from function"});
    // Sensor instructions
    registerInstruction({static_cast<uint32_t>(Opcode::ReadUltrasonic), "READ_ULTRASONIC", InstructionCategory::Sensor, Semantic::Native, 1, true, false, "Read ultrasonic distance"});
    registerInstruction({static_cast<uint32_t>(Opcode::ReadTouch), "READ_TOUCH", InstructionCategory::Sensor, Semantic::Native, 1, true, false, "Read touch sensor"});
    registerInstruction({static_cast<uint32_t>(Opcode::ReadLight), "READ_LIGHT", InstructionCategory::Sensor, Semantic::Native, 1, true, false, "Read light sensor"});
    registerInstruction({static_cast<uint32_t>(Opcode::ReadColor), "READ_COLOR", InstructionCategory::Sensor, Semantic::Native, 0, true, false, "Read color sensor"});
    registerInstruction({static_cast<uint32_t>(Opcode::ReadLine), "READ_LINE", InstructionCategory::Sensor, Semantic::Native, 2, true, false, "Read line sensor"});
    }

} // namespace execution
} // namespace robot