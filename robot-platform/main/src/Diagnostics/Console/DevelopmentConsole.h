#ifndef DEVELOPMENT_CONSOLE_H
#define DEVELOPMENT_CONSOLE_H

#include <stdint.h>

class DevelopmentConsole {
public:
    static DevelopmentConsole& instance();

    void begin(); // khởi tạo, mặc định enabled = true, rate = 10Hz
    void update(); // gọi trong loop, kiểm tra thời gian

    void setEnabled(bool enabled);
    bool isEnabled() const;
    void setRefreshRateHz(uint8_t hz);
    uint8_t getRefreshRateHz() const;

private:
    DevelopmentConsole() : _enabled(true), _refreshRateHz(10), _lastOutputTime(0) {}
    DevelopmentConsole(const DevelopmentConsole&) = delete;
    DevelopmentConsole& operator=(const DevelopmentConsole&) = delete;

    bool _enabled;
    uint8_t _refreshRateHz;
    uint32_t _lastOutputTime;

    uint32_t _getIntervalMs() const;
    void _output();
};

#endif