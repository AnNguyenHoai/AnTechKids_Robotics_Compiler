#include "program_loader.h"
#include "bytecode_reader.h"
#include "instruction_decoder.h"
#include <iostream>

namespace robot {
namespace execution {

ExecutionResult ProgramLoader::load(const uint8_t* bytecode, size_t size, Program& outProgram) {
    if (!bytecode || size == 0) {
        return ExecutionResult(ExecutionStatus::Failure, 1, "Invalid bytecode: null or empty");
    }

    // 1. Read bytecode
    BytecodeReader reader;
    if (!reader.load(bytecode, size)) {
        return ExecutionResult(ExecutionStatus::Failure, 2, "Bytecode read failed: " + reader.lastError());
    }

    // 2. Validate header
    auto headerResult = validateHeader(reader.header());
    if (!headerResult.isSuccess()) {
        return headerResult;
    }

    // 3. Decode instructions
    auto decodedInstrs = InstructionDecoder::decodeAll(reader.instructions());
    if (decodedInstrs.empty() && reader.instructions().size() > 0) {
        return ExecutionResult(ExecutionStatus::Failure, 3, "Failed to decode instructions");
    }

    // 4. Build Program
    Program program;
    program.setEntryPoint(reader.header().entryPoint);

    // Build constant pool
    ConstantPool pool;
    for (int32_t val : reader.constants()) {
        pool.addInteger(val);
    }
    program.setConstantPool(pool);

    // Build instruction list
    std::vector<ProgramInstruction> instrs;
    for (const auto& decoded : decodedInstrs) {
        ProgramInstruction instr;
        instr.opcode = decoded.opcode;
        instr.operands = decoded.operands;
        instrs.push_back(instr);
    }
    program.setInstructions(instrs);

    // 5. Validate entry point
    if (program.entryPoint() >= program.instructionCount() && program.instructionCount() > 0) {
        return ExecutionResult(ExecutionStatus::Failure, 4, "Invalid entry point");
    }

    outProgram = std::move(program);
    return ExecutionResult(ExecutionStatus::Success);
}

ExecutionResult ProgramLoader::load(const std::vector<uint8_t>& bytecode, Program& outProgram) {
    return load(bytecode.data(), bytecode.size(), outProgram);
}

ExecutionResult ProgramLoader::validateHeader(const BytecodeHeader& header) {
    if (header.magic != MAGIC_NUMBER) {
        return ExecutionResult(ExecutionStatus::Failure, 5, "Invalid magic number");
    }
    if (header.versionMajor != BYTECODE_VERSION_MAJOR) {
        return ExecutionResult(ExecutionStatus::Failure, 6, "Unsupported major version");
    }
    // Optionally check minor version
    return ExecutionResult(ExecutionStatus::Success);
}

} // namespace execution
} // namespace robots