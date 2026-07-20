#include "src/Application/RobotProgramApp.h"

VM vm;
Program program;

void setup()
{
    Serial.begin(115200);

    while (!Serial)
    {
    }

    Serial.println();
    Serial.println("==================================");
    Serial.println(" Robot VM Prototype");
    Serial.println("==================================");

    BuildProgram(program);

    vm.LoadProgram(&program);

    Serial.println("Program Loaded");
    Serial.println();
}

/******************************************************************************
 * Loop
 ******************************************************************************/

void loop()
{
    if (vm.IsRunning())
    {
        Serial.print("[VM] PC = ");
        Serial.println(vm.GetProgramCounter());

        vm.Step();

        delay(100);
    }
    else
    {
        Serial.println();
        Serial.println("========== VM FINISHED ==========");

        while (true)
        {
        }
    }
}