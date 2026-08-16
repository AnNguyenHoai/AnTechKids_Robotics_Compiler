#include "call_stack.h"

namespace robot {
namespace execution {

CallStack::CallStack(size_t maxDepth) : m_maxDepth(maxDepth) {
    m_frames.reserve(maxDepth);
}

void CallStack::pushFrame(const StackFrame& frame) {
    if (m_frames.size() >= m_maxDepth) {
        throw std::overflow_error("CallStack overflow");
    }
    m_frames.push_back(frame);
}

StackFrame CallStack::popFrame() {
    if (m_frames.empty()) {
        throw std::underflow_error("CallStack underflow");
    }
    StackFrame frame = m_frames.back();
    m_frames.pop_back();
    return frame;
}

StackFrame CallStack::currentFrame() const {
    if (m_frames.empty()) {
        throw std::runtime_error("CallStack empty");
    }
    return m_frames.back();
}

size_t CallStack::depth() const {
    return m_frames.size();
}

bool CallStack::empty() const {
    return m_frames.empty();
}

void CallStack::clear() {
    m_frames.clear();
}

} // namespace execution
} // namespace robot