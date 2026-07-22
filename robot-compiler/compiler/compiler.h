#pragma once
#include <string>
#include "packages/robot-common/include/Program.h"

/**
 * Top‑level compiler interface.
 * Currently throws "Not Implemented".
 */
class Compiler {
public:
    /**
     * Compile a source file to a Program (bytecode image).
     * @param filename Path to source file.
     * @return Program object containing functions and constants.
     * @throws std::runtime_error "Not Implemented" until later sprints.
     */
    Program compile(const std::string& filename);
};