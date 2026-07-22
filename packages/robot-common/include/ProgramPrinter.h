#pragma once
#include <iostream>
#include "Program.h"

/**
 * Prints a Program in human‑readable assembly format.
 * Example output:
 *   0000 MOVE_RUN forward 50
 *   0001 WAIT 1000
 *   0002 MOVE_STOP
 */
class ProgramPrinter {
public:
    static void print(const Program& program, std::ostream& out = std::cout);
};