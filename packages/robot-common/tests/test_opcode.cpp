#include <catch2/catch.hpp>
#include "Opcode.h"

TEST_CASE("Opcode size and values", "[opcode]") {
    REQUIRE(static_cast<int>(Opcode::MoveRun) == 0);
    REQUIRE(static_cast<int>(Opcode::COUNT) == 12);
}