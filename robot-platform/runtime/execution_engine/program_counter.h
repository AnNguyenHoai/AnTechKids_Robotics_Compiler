#pragma once

#include <cstdint>
#include <stdexcept>

namespace robot {
namespace execution {

class ProgramCounter {
public:
    ProgramCounter();

    void reset();
    void set(uint32_t address);
    uint32_t current() const;
    void next();
    void jump(uint32_t address);
    void increment();

    bool isValid() const;

private:
    uint32_t m_address;
    bool m_valid;
};

} // namespace execution
} // namespace robot