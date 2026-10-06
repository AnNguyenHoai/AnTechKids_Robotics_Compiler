#include "RobotHealthJsonSerializer.h"

#include <iomanip>
#include <sstream>

#include "../Health/BatteryMonitor.h"
#include "../Health/ResetReasonService.h"
#include "../Health/RobotHealthService.h"

std::string RobotHealthJsonSerializer::escape(const char* value) {
    std::string out;
    if (value == nullptr) return out;

    for (const unsigned char c : std::string(value)) {
        switch (c) {
            case '\\': out += "\\\\"; break;
            case '"': out += "\\\""; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (c < 0x20) {
                    std::ostringstream hex;
                    hex << "\\u"
                        << std::hex << std::uppercase << std::setw(4)
                        << std::setfill('0') << static_cast<unsigned>(c);
                    out += hex.str();
                } else {
                    out.push_back(static_cast<char>(c));
                }
                break;
        }
    }
    return out;
}

std::string RobotHealthJsonSerializer::serialize(
    const RobotHealth& health,
    const RobotHealthCompatibilityFields& compatibility
) {
    std::ostringstream out;
    out << std::fixed << std::setprecision(2);

    // Compatibility-critical V1 fields stay top-level and retain their names.
    out << "{\"status\":\"ok\""
        << ",\"ready\":" << boolText(compatibility.ready)
        << ",\"robot_ready\":" << boolText(compatibility.robotReady)
        << ",\"network_ready\":" << boolText(compatibility.networkReady)
        << ",\"ota\":" << boolText(compatibility.otaReady)
        << ",\"http_ota\":" << boolText(compatibility.httpOtaAvailable)
        << ",\"hostname\":\"" << escape(compatibility.hostname) << "\""
        << ",\"ip\":\"" << escape(health.network.ip) << "\"";

    // V2 aggregate-backed health fields.
    out << ",\"uptime_ms\":" << health.system.uptimeMs
        << ",\"firmware_version\":\"" << escape(health.system.firmwareVersion) << "\""
        << ",\"board_profile\":\"" << escape(health.system.boardProfile) << "\""
        << ",\"board_revision\":\"" << escape(health.system.boardRevision) << "\""
        << ",\"reset_reason\":\"" << ResetReasonService::nameOf(health.system.resetReason) << "\"";

    out << ",\"battery\":{"
        << "\"voltage\":" << health.battery.voltage
        << ",\"state\":\"" << BatteryMonitor::stateName(health.battery.state) << "\"}";

    out << ",\"motor\":{"
        << "\"armed\":" << boolText(health.motor.armed)
        << ",\"enabled\":" << boolText(health.motor.enabled)
        << ",\"state\":\"" << RobotHealthService::motorStateName(health.motor.state) << "\""
        << ",\"last_stop_reason\":\"" << RobotHealthService::motorStopReasonName(health.motor.lastStopReason) << "\"}";

    out << ",\"start\":{"
        << "\"pressed\":" << boolText(health.start.pressed)
        << ",\"ready_for_press\":" << boolText(health.start.readyForPress)
        << ",\"armed_by_start_this_boot\":" << boolText(health.start.armedByStartThisBoot) << "}";

    out << ",\"line\":{"
        << "\"available\":" << boolText(health.line.available)
        << ",\"healthy\":" << boolText(health.line.healthy)
        << ",\"mask\":" << static_cast<unsigned>(health.line.mask) << "}"
        << ",\"line_mask\":" << static_cast<unsigned>(health.line.mask);

    out << ",\"encoder\":{"
        << "\"available\":" << boolText(health.encoder.available)
        << ",\"healthy\":" << boolText(health.encoder.healthy) << "}";

    out << ",\"i2c\":{"
        << "\"healthy\":" << boolText(health.i2c.healthy)
        << ",\"mcp23017\":" << boolText(health.i2c.mcp23017) << "}"
        << ",\"i2c_ok\":" << boolText(health.i2c.healthy);

    out << ",\"rssi\":" << health.network.rssi
        << "}";

    return out.str();
}
