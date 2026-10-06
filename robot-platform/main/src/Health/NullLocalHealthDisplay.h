#pragma once

#include "ILocalHealthDisplay.h"

class NullLocalHealthDisplay : public ILocalHealthDisplay {
public:
    bool begin() override { return false; }
    bool render(const LocalHealthDisplayFrame&) override { return false; }
};
