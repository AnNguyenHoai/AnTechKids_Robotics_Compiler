#include <catch2/catch.hpp>
#include "ProgramPrinter.h"
#include <sstream>

TEST_CASE("ProgramPrinter output", "[printer]") {
    Program p;
    Function f("main");
    f.instructions.emplace_back(Opcode::MoveRun,
                                std::vector<Operand>{Operand("forward"), Operand(50)});
    f.instructions.emplace_back(Opcode::Wait, std::vector<Operand>{Operand(1000)});
    f.instructions.emplace_back(Opcode::MoveStop);
    p.functions.push_back(f);

    std::stringstream ss;
    ProgramPrinter::print(p, ss);
    std::string output = ss.str();

    REQUIRE(output.find("Function: main") != std::string::npos);
    REQUIRE(output.find("MOVE_RUN") != std::string::npos);
    REQUIRE(output.find("forward") != std::string::npos);
    REQUIRE(output.find("50") != std::string::npos);
    REQUIRE(output.find("WAIT") != std::string::npos);
    REQUIRE(output.find("1000") != std::string::npos);
    REQUIRE(output.find("MOVE_STOP") != std::string::npos);
}