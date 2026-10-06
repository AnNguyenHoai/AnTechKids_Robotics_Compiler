#include "MCP23017Platform.h"
#include "MCP23017WireTransport.h"

MCP23017Driver& systemMCP23017() {
    static MCP23017WireTransport transport;
    static MCP23017Driver driver(transport);
    return driver;
}
