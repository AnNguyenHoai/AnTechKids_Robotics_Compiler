#include <catch2/catch.hpp>
#include "Program.h"

TEST_CASE("Program construction", "[program]") {
    Program p;
    REQUIRE(p.functions.empty());
    REQUIRE(p.constants.size() == 0);

    Function f("main");
    p.functions.push_back(f);
    REQUIRE(p.functions.size() == 1);
}