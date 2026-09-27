#include "LineRegressionTelemetry.h"

#include <Arduino.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#ifndef LINE_REGRESSION_DIAGNOSTICS
#define LINE_REGRESSION_DIAGNOSTICS 0
#endif

#ifndef LINE_REGRESSION_UDP
#define LINE_REGRESSION_UDP 0
#endif

#if LINE_REGRESSION_UDP
#include <WiFi.h>
#include <WiFiUdp.h>
#endif

namespace {
constexpr size_t kRecordSize = 320;
constexpr uint8_t kQueueCapacity = 16;

#if LINE_REGRESSION_DIAGNOSTICS
char g_queue[kQueueCapacity][kRecordSize] = {};
uint8_t g_head = 0;
uint8_t g_count = 0;
uint32_t g_dropped = 0;

void enqueueRecord(const char* record) {
    if (g_count == kQueueCapacity) {
        g_head = static_cast<uint8_t>((g_head + 1U) % kQueueCapacity);
        --g_count;
        ++g_dropped;
    }

    const uint8_t tail = static_cast<uint8_t>((g_head + g_count) % kQueueCapacity);
    strncpy(g_queue[tail], record, kRecordSize - 1U);
    g_queue[tail][kRecordSize - 1U] = '\0';
    ++g_count;
}
#endif

#if LINE_REGRESSION_UDP
constexpr uint16_t kUdpDestinationPort = 4211;
constexpr uint16_t kUdpSourcePort = 4212;
WiFiUDP g_udp;
bool g_udpReady = false;

IPAddress subnetBroadcast() {
    const IPAddress ip = WiFi.localIP();
    const IPAddress mask = WiFi.subnetMask();
    return IPAddress(
        static_cast<uint8_t>(ip[0] | static_cast<uint8_t>(~mask[0])),
        static_cast<uint8_t>(ip[1] | static_cast<uint8_t>(~mask[1])),
        static_cast<uint8_t>(ip[2] | static_cast<uint8_t>(~mask[2])),
        static_cast<uint8_t>(ip[3] | static_cast<uint8_t>(~mask[3]))
    );
}

bool ensureUdpReady() {
    if (WiFi.status() != WL_CONNECTED) {
        if (g_udpReady) {
            g_udp.stop();
            g_udpReady = false;
        }
        return false;
    }

    if (!g_udpReady) {
        g_udpReady = g_udp.begin(kUdpSourcePort);
    }
    return g_udpReady;
}
#endif
}

namespace LineRegressionTelemetry {

void Emit(const char* format, ...) {
#if LINE_REGRESSION_DIAGNOSTICS
    char record[kRecordSize];
    va_list args;
    va_start(args, format);
    vsnprintf(record, sizeof(record), format, args);
    va_end(args);

    // Preserve the original bench-debug path. At the sparse LINE-REG emission
    // rate this remains useful when USB is attached, while wireless capture is
    // buffered independently for untethered physical qualification.
    Serial.println(record);

#if LINE_REGRESSION_UDP
    enqueueRecord(record);
#endif
#else
    (void)format;
#endif
}

void Update() {
#if LINE_REGRESSION_DIAGNOSTICS && LINE_REGRESSION_UDP
    if (g_count == 0 || !ensureUdpReady()) {
        return;
    }

    const char* record = g_queue[g_head];
    const size_t length = strnlen(record, kRecordSize);
    if (length == 0) {
        g_head = static_cast<uint8_t>((g_head + 1U) % kQueueCapacity);
        --g_count;
        return;
    }

    const IPAddress destination = subnetBroadcast();
    if (!g_udp.beginPacket(destination, kUdpDestinationPort)) {
        return;
    }
    g_udp.write(reinterpret_cast<const uint8_t*>(record), length);
    g_udp.write(static_cast<uint8_t>('\n'));
    if (!g_udp.endPacket()) {
        return;
    }

    g_head = static_cast<uint8_t>((g_head + 1U) % kQueueCapacity);
    --g_count;

    // Surface queue pressure without emitting recursively through this logger.
    // The count is intentionally only printed on the wired fallback channel.
    if (g_dropped != 0 && g_count == 0) {
        Serial.printf("[LINE-REG][TRANSPORT] dropped=%lu\n", static_cast<unsigned long>(g_dropped));
        g_dropped = 0;
    }
#endif
}

}  // namespace LineRegressionTelemetry
