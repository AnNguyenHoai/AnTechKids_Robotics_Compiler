#ifndef SENSOR_QUADRATUREDECODER_H
#define SENSOR_QUADRATUREDECODER_H

#include <stdint.h>

/**
 * Stateless transition decoder for a two-channel quadrature encoder.
 * State encoding is (A << 1) | B. Each valid edge contributes +/-1 count.
 * Invalid transitions (both bits changing at once) are ignored.
 */
class QuadratureDecoder {
public:
    static int8_t transition(int previousState, int currentState) {
        static constexpr int8_t table[16] = {
             0, +1, -1,  0,
            -1,  0,  0, +1,
            +1,  0,  0, -1,
             0, -1, +1,  0
        };
        return table[((previousState & 0x3) << 2) | (currentState & 0x3)];
    }
};

#endif // SENSOR_QUADRATUREDECODER_H
