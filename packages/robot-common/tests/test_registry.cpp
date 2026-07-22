#include <catch2/catch.hpp>
#include "OpcodeRegistry.h"

TEST_CASE("OpcodeRegistry metadata", "[registry]") {
    auto& reg = OpcodeRegistry::instance();

    REQUIRE(reg.getName(Opcode::MoveRun) == "MOVE_RUN");
    REQUIRE(reg.getOperandCount(Opcode::MoveRun) == 2);
    REQUIRE(reg.getDescription(Opcode::MoveRun) == "Start continuous movement");

    REQUIRE(reg.getName(Opcode::MoveStop) == "MOVE_STOP");
    REQUIRE(reg.getOperandCount(Opcode::MoveStop) == 0);
    REQUIRE(reg.getDescription(Opcode::MoveStop) == "Stop all motion");
}