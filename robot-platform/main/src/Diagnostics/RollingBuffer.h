#ifndef ROLLING_BUFFER_H
#define ROLLING_BUFFER_H

#include <stddef.h>
#include <stdint.h>

template<size_t N>
class RollingBuffer {
public:
    RollingBuffer() : head(0), count(0) {}

    void push(bool value) {
        buffer[head] = value ? 1 : 0;
        head = (head + 1) % N;
        if (count < N) count++;
    }

    size_t size() const { return count; }

    size_t highCount() const {
        size_t h = 0;
        for (size_t i = 0; i < count; i++) {
            if (buffer[i]) h++;
        }
        return h;
    }

    float stability() const {
        if (count == 0) return 100.0f;
        return (highCount() * 100.0f) / count;
    }

private:
    uint8_t buffer[N];
    size_t head;
    size_t count;
};

#endif