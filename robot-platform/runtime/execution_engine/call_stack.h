#pragma once

#include <vector>
#include <cstdint>
#include <stdexcept>

namespace robot {
namespace execution {

struct StackFrame {
    uint32_t returnAddress;
    uint32_t framePointer;
    uint32_t localVariableCount;
    // Additional fields can be added later (e.g., local variable table pointer)
};

class CallStack {
public:
    explicit CallStack(size_t maxDepth = 64);

    void pushFrame(const StackFrame& frame);
    StackFrame popFrame();
    StackFrame currentFrame() const;
    size_t depth() const;
    bool empty() const;
    void clear();

private:
    std::vector<StackFrame> m_frames;
    size_t m_maxDepth;
};

} // namespace execution
} // namespace robot