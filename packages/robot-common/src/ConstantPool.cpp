#include "ConstantPool.h"
#include <algorithm>

uint32_t ConstantPool::add(int64_t v)         { return findOrAdd(v); }
uint32_t ConstantPool::add(double v)          { return findOrAdd(v); }
uint32_t ConstantPool::add(const std::string& v) { return findOrAdd(v); }
uint32_t ConstantPool::add(bool v)            { return findOrAdd(v); }

const ConstantPool::Constant& ConstantPool::get(uint32_t index) const {
    return constants.at(index);
}

template<typename T>
uint32_t ConstantPool::findOrAdd(const T& value) {
    Constant c(value);
    auto it = std::find(constants.begin(), constants.end(), c);
    if (it != constants.end()) {
        return static_cast<uint32_t>(it - constants.begin());
    }
    constants.push_back(c);
    return static_cast<uint32_t>(constants.size() - 1);
}