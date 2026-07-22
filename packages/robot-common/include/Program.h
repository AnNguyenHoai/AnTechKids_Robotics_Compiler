#pragma once
#include <vector>
#include "Function.h"
#include "ConstantPool.h"

/**
 * A program is the compiler's output before binary encoding.
 * Contains a constant pool and a list of functions.
 */
class Program {
public:
    ConstantPool constants;
    std::vector<Function> functions;
};