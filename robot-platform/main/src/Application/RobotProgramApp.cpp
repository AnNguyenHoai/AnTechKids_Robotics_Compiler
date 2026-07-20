#include "RobotProgramApp.h"
#include "generated_program.h"

void BuildProgram(Program& program)
{
    program.Clear();

    for (uint16_t i = 0; i < generatedProgramSize; i++)
    {
        program.AddInstruction(generatedProgram[i]);
    }
}