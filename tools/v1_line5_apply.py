from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one baseline match, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    '#include "../../Services/Line/LineFollower.h"\n',
    '#include "../../Services/Line/LineFollower.h"\n#include "../../Services/Line/LineSensorLayout.h"\n',
    "line layout include",
)

replace_once(
'''int16_t ReadLine(int channel) {
    SensorID id;
    switch (channel) {
        case 0: id = SensorID::LineLeft; break;
        case 1: id = SensorID::LineCenter; break;
        case 2: id = SensorID::LineRight; break;
        default: return 0;
    }
    auto sensor = SensorManager::instance().getSensor(id);
    if (sensor) {
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        return lineSensor->isLineDetected() ? 1 : 0;
    }
    return 0;
}
''',
'''int16_t ReadLine(int channel) {
    SensorID id;
    if (!LineSensorLayout::sensorIdFromChannel(channel, id)) return 0;

    auto sensor = SensorManager::instance().getSensor(id);
    if (!sensor) return 0;

    auto lineSensor = static_cast<TCRT5000*>(sensor);
    lineSensor->update();
    return lineSensor->isLineDetected() ? 1 : 0;
}
''',
    "ReadLine channel mapping",
)

replace_once(
'''int16_t GetTraceValue(int port, int channel) {
#if !ROBOT_FEATURE_LINE_SENSOR
    (void)port; (void)channel;
    return 0;
#else
    SensorID id;
    switch (channel) {
        case 0: id = SensorID::LineLeft; break;
        case 1: id = SensorID::LineCenter; break;
        case 2: id = SensorID::LineRight; break;
        default: return 0;
    }
    auto sensor = SensorManager::instance().getSensor(id);
    if (sensor) {
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        return lineSensor->isLineDetected() ? 100 : 0;
    }
    return 0;
#endif
}
''',
'''int16_t GetTraceValue(int port, int channel) {
#if !ROBOT_FEATURE_LINE_SENSOR
    (void)port; (void)channel;
    return 0;
#else
    (void)port;
    SensorID id;
    if (!LineSensorLayout::sensorIdFromChannel(channel, id)) return 0;

    auto sensor = SensorManager::instance().getSensor(id);
    if (!sensor) return 0;

    auto lineSensor = static_cast<TCRT5000*>(sensor);
    lineSensor->update();
    return lineSensor->isLineDetected() ? 100 : 0;
#endif
}
''',
    "GetTraceValue channel mapping",
)

replace_once(
'''bool GetTraceState(int port, int channel) {
#if !ROBOT_FEATURE_LINE_SENSOR
    (void)port; (void)channel;
    return false;
#else
    SensorID id;
    switch (channel) {
        case 0: id = SensorID::LineLeft; break;
        case 1: id = SensorID::LineCenter; break;
        case 2: id = SensorID::LineRight; break;
        default: return false;
    }
    auto sensor = SensorManager::instance().getSensor(id);
    if (sensor) {
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        return lineSensor->isLineDetected();
    }
    return false;
#endif
}
''',
'''bool GetTraceState(int port, int channel) {
#if !ROBOT_FEATURE_LINE_SENSOR
    (void)port; (void)channel;
    return false;
#else
    (void)port;
    SensorID id;
    if (!LineSensorLayout::sensorIdFromChannel(channel, id)) return false;

    auto sensor = SensorManager::instance().getSensor(id);
    if (!sensor) return false;

    auto lineSensor = static_cast<TCRT5000*>(sensor);
    lineSensor->update();
    return lineSensor->isLineDetected();
#endif
}
''',
    "GetTraceState channel mapping",
)

replace_once(
'''int16_t GetTraceRaw(int port) {
#if !ROBOT_FEATURE_LINE_SENSOR
    (void)port;
    return 0;
#else
    int mask = 0;
    auto left = SensorManager::instance().getSensor(SensorID::LineLeft);
    auto center = SensorManager::instance().getSensor(SensorID::LineCenter);
    auto right = SensorManager::instance().getSensor(SensorID::LineRight);
    if (left) {
        auto l = static_cast<TCRT5000*>(left);
        l->update();
        if (l->isLineDetected()) mask |= 4;
    }
    if (center) {
        auto c = static_cast<TCRT5000*>(center);
        c->update();
        if (c->isLineDetected()) mask |= 2;
    }
    if (right) {
        auto r = static_cast<TCRT5000*>(right);
        r->update();
        if (r->isLineDetected()) mask |= 1;
    }
    return mask;
#endif
}
''',
'''int16_t GetTraceRaw(int port) {
#if !ROBOT_FEATURE_LINE_SENSOR
    (void)port;
    return 0;
#else
    (void)port;
    uint8_t mask = 0;

    struct Entry { SensorID id; uint8_t bit; };
    static const Entry entries[] = {
        {SensorID::LineFarLeft,  LineSensorLayout::MASK_FAR_LEFT},
        {SensorID::LineLeft,     LineSensorLayout::MASK_LEFT},
        {SensorID::LineCenter,   LineSensorLayout::MASK_CENTER},
        {SensorID::LineRight,    LineSensorLayout::MASK_RIGHT},
        {SensorID::LineFarRight, LineSensorLayout::MASK_FAR_RIGHT},
    };

    auto& manager = SensorManager::instance();
    for (const auto& entry : entries) {
        auto sensor = manager.getSensor(entry.id);
        if (!sensor) continue;
        auto lineSensor = static_cast<TCRT5000*>(sensor);
        lineSensor->update();
        if (lineSensor->isLineDetected()) mask |= entry.bit;
    }
    return mask;
#endif
}
''',
    "GetTraceRaw five-bit mask",
)

replace_once(
'''#if ROBOT_FEATURE_LINE_SENSOR
    mgr.registerSensor(SensorID::LineLeft,
                       new TCRT5000(SENSOR_TRCT5000_L_PIN, "line_left"));
    mgr.registerSensor(SensorID::LineCenter,
                       new TCRT5000(SENSOR_TRCT5000_C_PIN, "line_center"));
    mgr.registerSensor(SensorID::LineRight,
                       new TCRT5000(SENSOR_TRCT5000_R_PIN, "line_right"));
#endif
''',
'''#if ROBOT_FEATURE_LINE_SENSOR
    mgr.registerSensor(SensorID::LineFarLeft,
                       new TCRT5000(SENSOR_TRCT5000_FL_PIN, "line_far_left"));
    mgr.registerSensor(SensorID::LineLeft,
                       new TCRT5000(SENSOR_TRCT5000_L_PIN, "line_left"));
    mgr.registerSensor(SensorID::LineCenter,
                       new TCRT5000(SENSOR_TRCT5000_C_PIN, "line_center"));
    mgr.registerSensor(SensorID::LineRight,
                       new TCRT5000(SENSOR_TRCT5000_R_PIN, "line_right"));
    mgr.registerSensor(SensorID::LineFarRight,
                       new TCRT5000(SENSOR_TRCT5000_FR_PIN, "line_far_right"));
#endif
''',
    "five sensor registration",
)

# Make diagnostic output unambiguous now that raw masks occupy five bits.
replace_once(
    '"[LINE-RESPONSE] t=%luus mask=%03u prev=%s loop=%luus | sensor=%luus control=%luus output=%luus total=%luus | cmd L=%d R=%d\\n",',
    '"[LINE-RESPONSE] t=%luus mask=0x%02X prev=%s loop=%luus | sensor=%luus control=%luus output=%luus total=%luus | cmd L=%d R=%d\\n",',
    "line response mask format",
)

path.write_text(text, encoding="utf-8")
print("PASS: V1-LINE5 RobotAPI patch applied with baseline assertions")
