#include "LinePerception.h"

LineState LinePerception::interpret(uint8_t mask) {
    mask &= LineMask::ALL;
    switch (mask) {
        case 0:                              return LineState::LOST;
        case LineMask::CENTER:               return LineState::CENTER;
        case LineMask::LEFT:                 return LineState::LEFT;
        case LineMask::RIGHT:                return LineState::RIGHT;
        case LineMask::LEFT | LineMask::CENTER:
                                             return LineState::LEFT_CENTER;
        case LineMask::CENTER | LineMask::RIGHT:
                                             return LineState::CENTER_RIGHT;
        case LineMask::ALL:                  return LineState::INTERSECTION;
        // LEFT|RIGHT with no center is intentionally ambiguous rather than
        // being silently classified as an intersection. This preserves the
        // existing controller behavior while making the mask contract explicit.
        default:                             return LineState::UNKNOWN;
    }
}