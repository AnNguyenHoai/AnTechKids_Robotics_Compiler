#include <assert.h>
#include "../main/src/Sensor/QuadratureDecoder.h"

int main() {
    // Forward: 00 -> 01 -> 11 -> 10 -> 00
    assert(QuadratureDecoder::transition(0, 1) == +1);
    assert(QuadratureDecoder::transition(1, 3) == +1);
    assert(QuadratureDecoder::transition(3, 2) == +1);
    assert(QuadratureDecoder::transition(2, 0) == +1);

    // Reverse
    assert(QuadratureDecoder::transition(0, 2) == -1);
    assert(QuadratureDecoder::transition(2, 3) == -1);
    assert(QuadratureDecoder::transition(3, 1) == -1);
    assert(QuadratureDecoder::transition(1, 0) == -1);

    // No movement / invalid jump
    assert(QuadratureDecoder::transition(0, 0) == 0);
    assert(QuadratureDecoder::transition(0, 3) == 0);
    assert(QuadratureDecoder::transition(1, 2) == 0);
    return 0;
}
