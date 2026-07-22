#include <catch2/catch.hpp>
#include "Function.h"

TEST_CASE("Function construction", "[function]") {
    Function f("task1");
    REQUIRE(f.name == "task1");
    REQUIRE(f.instructions.empty());

    f.instructions.emplace_back(Opcode::MoveRun);
    REQUIRE(f.instructions.size() == 1);
}