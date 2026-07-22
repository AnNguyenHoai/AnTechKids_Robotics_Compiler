#include <catch2/catch.hpp>
#include "ConstantPool.h"

TEST_CASE("ConstantPool deduplication", "[constantpool]") {
    ConstantPool pool;
    auto idx1 = pool.add(42);
    auto idx2 = pool.add(42);
    REQUIRE(idx1 == idx2);
    REQUIRE(pool.size() == 1);

    auto idx3 = pool.add(3.14);
    REQUIRE(idx3 != idx1);
    REQUIRE(pool.size() == 2);

    auto idx4 = pool.add(std::string("hello"));
    REQUIRE(idx4 == 2);
    REQUIRE(pool.size() == 3);

    auto idx5 = pool.add(true);
    REQUIRE(idx5 == 3);
    REQUIRE(pool.size() == 4);
}