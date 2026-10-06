from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINE = ROOT / "robot-platform/main/src/Services/Line"
HAL = ROOT / "robot-platform/main/src/HardwareAbstraction"
ROBOT_API = ROOT / "robot-platform/main/src/Services/Robot/RobotAPI.cpp"
GPIO = HAL / "GPIO.h"

HARNESS = r"""
#include <cassert>
#include <cstdint>
#include <map>
#include "MCP23017Driver.h"
#include "LineSensorBank.h"

struct FakeTransport : IMCP23017Transport {
    bool busOk=true, present=true, failRead=false, failWrite=false;
    std::map<uint8_t,uint8_t> regs;
    int gpioAReads=0;
    bool ensureBusInitialized() override { return busOk; }
    bool probe(uint8_t) override { return present; }
    bool writeRegister(uint8_t,uint8_t reg,uint8_t value) override {
        if (failWrite) return false;
        regs[reg] = value;
        return true;
    }
    bool readRegister(uint8_t,uint8_t reg,uint8_t& value) override {
        if(failRead) return false;
        if(reg==0x12) gpioAReads++;
        value=regs[reg]; return true;
    }
};

int main() {
    FakeTransport t;
    MCP23017Driver mcp(t);
    LineSensorBank bank(mcp);
    assert(bank.begin());
    assert(mcp.begin()); // idempotent; must not reset configured state

    struct Case { uint8_t physical; uint8_t canonical; };
    const Case cases[] = {
        {0b00001,0b10000},{0b00010,0b01000},{0b00100,0b00100},
        {0b01000,0b00010},{0b10000,0b00001},{0b11111,0b11111},{0,0}
    };
    for(const auto& c:cases) {
        t.regs[0x12]=c.physical;
        int before=t.gpioAReads;
        uint8_t mask=0xFF;
        assert(bank.readMask(mask));
        assert(mask==c.canonical);
        assert(t.gpioAReads==before+1);
        bool d=false;
        assert(bank.channel(0,d) && d==((c.canonical&0x08)!=0));
        assert(bank.channel(1,d) && d==((c.canonical&0x04)!=0));
        assert(bank.channel(2,d) && d==((c.canonical&0x02)!=0));
        assert(bank.channel(3,d) && d==((c.canonical&0x10)!=0));
        assert(bank.channel(4,d) && d==((c.canonical&0x01)!=0));
    }
    bool d=true;
    assert(!bank.channel(5,d) && !d);
    t.failRead=true;
    uint8_t mask=0xFF;
    assert(!bank.readMask(mask) && mask==0 && !bank.healthy());
    return 0;
}
"""

def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        src=td/"line_bank_test.cpp"
        exe=td/"line_bank_test"
        src.write_text(HARNESS,encoding="utf-8")
        subprocess.run(["g++","-std=c++11","-Wall","-Wextra","-Werror",
            "-I",str(HAL),"-I",str(LINE),str(src),str(LINE/"LineSensorBank.cpp"),
            str(HAL/"MCP23017Driver.cpp"),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
    print("PASS: physical GPA0..4 -> canonical FL/L/C/R/FR conversion")
    api=ROBOT_API.read_text(encoding="utf-8")
    gpio=GPIO.read_text(encoding="utf-8")
    assert "new TCRT5000(" not in api
    assert "SENSOR_TRCT5000_" not in api and "SENSOR_TRCT5000_" not in gpio
    start=api.index("int16_t GetTraceRaw")
    end=api.index("// ===== Initialization =====",start)
    raw=api[start:end]
    assert raw.count("g_lineSensorBank.readMask(")==1
    assert "SensorManager::instance()" not in raw
    print("PASS: RobotAPI raw path uses one LineSensorBank Port-A acquisition")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
