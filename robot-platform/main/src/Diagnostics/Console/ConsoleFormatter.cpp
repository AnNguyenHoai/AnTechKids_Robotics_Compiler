#include "ConsoleFormatter.h"

String ConsoleFormatter::format(const ConsoleData& data) {
    String out;
    out += "====================================\n";
    out += "ROBOT DIAGNOSTICS\n";
    out += "------------------------------------\n";
    out += "Sensors\n";
    out += "LEFT      ";
    out += data.leftState ? "HIGH" : "LOW";
    out += "\n";
    out += "CENTER    ";
    out += data.centerState ? "HIGH" : "LOW";
    out += "\n";
    out += "RIGHT     ";
    out += data.rightState ? "HIGH" : "LOW";
    out += "\n";
    out += "MASK      ";
    // In ra dạng nhị phân 3 bit
    out += String(data.mask, BIN);
    out += "\n";
    out += "------------------------------------\n";
    out += "Statistics\n";

    auto printSensorStat = [&](const char* name, const SensorStatistics& stat) {
        out += name;
        out += "\n";
        out += "Reads          ";
        out += String(stat.readCount);
        out += "\n";
        out += "Transitions    ";
        out += String(stat.transitionCount);
        out += "\n";
        out += "Stability      ";
        out += String(stat.stability, 1);
        out += "%\n";
    };
    printSensorStat("LEFT", data.leftStat);
    printSensorStat("CENTER", data.centerStat);
    printSensorStat("RIGHT", data.rightStat);

    // Sensor Health heuristic
    auto healthString = [](const SensorStatistics& stat) -> const char* {
        float stability = stat.stability;
        uint32_t reads = stat.readCount;
        uint32_t transitions = stat.transitionCount;
        float transitionRate = (reads > 0) ? (float)transitions / reads : 0.0f;
        if (stability < 90.0f || transitionRate > 0.02f) {
            return "NOISY";
        } else {
            return "STABLE";
        }
    };
    out += "Health\n";
    out += "LEFT      ";
    out += healthString(data.leftStat);
    out += "\n";
    out += "CENTER    ";
    out += healthString(data.centerStat);
    out += "\n";
    out += "RIGHT     ";
    out += healthString(data.rightStat);
    out += "\n";

    out += "------------------------------------\n";
    out += "Runtime\n";
    out += "Loop Time  ";
    out += String(data.lastLoopUs / 1000.0f, 2);
    out += " ms\n";
    out += "Loop Freq  ";
    out += String(data.loopFreq, 1);
    out += " Hz\n";
    out += "Tick       ";
    out += String(data.tickCount);
    out += "\n";
    out += "Min Loop   ";
    out += String(data.minLoopUs / 1000.0f, 2);
    out += " ms\n";
    out += "Max Loop   ";
    out += String(data.maxLoopUs / 1000.0f, 2);
    out += " ms\n";
    out += "====================================\n";
    return out;
}