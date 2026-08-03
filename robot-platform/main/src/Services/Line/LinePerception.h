#ifndef LINE_PERCEPTION_H
#define LINE_PERCEPTION_H

#include <stdint.h>
#include "LineState.h"

class LinePerception {
public:
    static LineState interpret(uint8_t mask);
};

#endif // LINE_PERCEPTION_H