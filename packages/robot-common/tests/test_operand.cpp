#include <catch2/catch.hpp>
#include "Operand.h"

TEST_CASE("Operand construction", "[operand]") {
    Operand intOp(42);
    REQUIRE(intOp.getType() == OperandType::Integer);
    REQUIRE(intOp.asInteger() == 42);

    Operand floatOp(3.14);
    REQUIRE(floatOp.getType() == OperandType::Float);
    REQUIRE(floatOp.asFloat() == 3.14);

    Operand boolOp(true);
    REQUIRE(boolOp.getType() == OperandType::Boolean);
    REQUIRE(boolOp.asBoolean() == true);

    Operand strOp("hello");
    REQUIRE(strOp.getType() == OperandType::String);
    REQUIRE(strOp.asString() == "hello");

    Operand varOp(5, OperandType::Variable);
    REQUIRE(varOp.getType() == OperandType::Variable);
    REQUIRE(varOp.asIndex() == 5);
}