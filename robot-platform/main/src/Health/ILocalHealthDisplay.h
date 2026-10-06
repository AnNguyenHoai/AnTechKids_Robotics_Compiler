#pragma once

#include <stdint.h>

struct LocalHealthDisplayFrame {
    const char* line1 = "";
    const char* line2 = "";
    const char* line3 = "";
    const char* line4 = "";
};

class ILocalHealthDisplay {
public:
    virtual ~ILocalHealthDisplay() = default;

    // Missing/unsupported display returns false and must never block runtime.
    virtual bool begin() = 0;
    virtual bool render(const LocalHealthDisplayFrame& frame) = 0;
};
