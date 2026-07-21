#include "src/Services/VM/ProgramLoader.h"

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

    // Load program from generated header
    ProgramLoader::LoadFromGenerated(program);

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