#include "LinePerception.h"

LineState LinePerception::interpret(uint8_t mask) {
    mask &= 0b111;
    switch (mask) {
        case 0b000: return LineState::LOST;
        case 0b010: return LineState::CENTER;
        case 0b100: return LineState::LEFT;
        case 0b001: return LineState::RIGHT;
        case 0b110: return LineState::LEFT_CENTER;
        case 0b011: return LineState::CENTER_RIGHT;
        case 0b111: return LineState::INTERSECTION;
        default:    return LineState::UNKNOWN;
    }
}