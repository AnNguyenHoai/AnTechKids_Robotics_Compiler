# Behavior Development Guide

## Creating a new Behavior
1. Kế thừa lớp `Behavior`.
2. Implement các phương thức lifecycle.
3. Sử dụng `BehaviorContext` để truy cập runtime.
4. Đăng ký behavior vào scheduler.

## Example
```cpp
class MyBehavior : public Behavior {
public:
    MyBehavior() { name = "MyBehavior"; }
    void init(BehaviorContext& ctx) override { setStatus(BehaviorStatus::INITIALIZED); }
    void start(BehaviorContext& ctx) override { ... }
    void update(BehaviorContext& ctx) override { ... }
    // ... các phương thức khác
};