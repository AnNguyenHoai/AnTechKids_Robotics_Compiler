#include "program_counter.h"

namespace robot {
namespace execution {

ProgramCounter::ProgramCounter() : m_address(0), m_valid(false) {}

void ProgramCounter::reset() {
    m_address = 0;
    m_valid = false;
}

void ProgramCounter::set(uint32_t address) {
    m_address = address;
    m_valid = true;
}

uint32_t ProgramCounter::current() const {
    if (!m_valid) throw std::runtime_error("Program counter not set");
    return m_address;
}

void ProgramCounter::next() {
    if (!m_valid) throw std::runtime_error("Program counter not set");
    m_address++;
}

void ProgramCounter::jump(uint32_t address) {
    m_address = address;
    m_valid = true;
}

void ProgramCounter::increment() {
    if (!m_valid) throw std::runtime_error("Program counter not set");
    m_address++;
}

bool ProgramCounter::isValid() const {
    return m_valid;
}

} // namespace execution
} // namespace robot