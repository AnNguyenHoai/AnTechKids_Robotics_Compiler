#include <catch2/catch.hpp>
#include "Instruction.h"

TEST_CASE("Instruction construction", "[instruction]") {
    Instruction ins(Opcode::MoveRun);
    REQUIRE(ins.opcode == Opcode::MoveRun);
    REQUIRE(ins.operands.empty());

    Instruction ins2(Opcode::Wait, {Operand(1000)});
    REQUIRE(ins2.opcode == Opcode::Wait);
    REQUIRE(ins2.operands.size() == 1);
    REQUIRE(ins2.operands[0].asInteger() == 1000);
}