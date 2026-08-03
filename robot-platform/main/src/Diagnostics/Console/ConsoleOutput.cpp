#include "ConsoleOutput.h"

void ConsoleOutput::begin() {
    // Serial đã được khởi tạo trong setup
}

void ConsoleOutput::print(const String& message) {
    Serial.print(message);
}