#ifndef LINE_STATE_H
#define LINE_STATE_H

#include <stdint.h>

enum class LineState : uint8_t {
    LOST,
    CENTER,
    LEFT,
    RIGHT,
    LEFT_CENTER,
    CENTER_RIGHT,
    INTERSECTION,
    UNKNOWN
};

#endif // LINE_STATE_H