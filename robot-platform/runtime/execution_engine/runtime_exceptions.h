#pragma once

#include <stdexcept>
#include <string>

namespace robot {
namespace execution {

class RuntimeException : public std::runtime_error {
public:
    explicit RuntimeException(const std::string& msg) : std::runtime_error(msg) {}
};

class StackOverflowException : public RuntimeException {
public:
    explicit StackOverflowException(const std::string& msg = "Stack overflow") : RuntimeException(msg) {}
};

class StackUnderflowException : public RuntimeException {
public:
    explicit StackUnderflowException(const std::string& msg = "Stack underflow") : RuntimeException(msg) {}
};

class VariableNotFoundException : public RuntimeException {
public:
    explicit VariableNotFoundException(const std::string& msg = "Variable not found") : RuntimeException(msg) {}
};

class InvalidProgramCounterException : public RuntimeException {
public:
    explicit InvalidProgramCounterException(const std::string& msg = "Invalid program counter") : RuntimeException(msg) {}
};

class ExecutionStateException : public RuntimeException {
public:
    explicit ExecutionStateException(const std::string& msg = "Invalid execution state") : RuntimeException(msg) {}
};

} // namespace execution
} // namespace robot