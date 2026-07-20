/******************************************************************************
 * File        : VM.cpp
 *
 * Description :
 *      Robot Virtual Machine Implementation.
 *
 ******************************************************************************/

#include "VM.h"

#include "../Robot/RobotAPI.h"

/******************************************************************************
 * Constructor
 ******************************************************************************/

VM::VM()
    : mProgram(nullptr)
{
}

/******************************************************************************
 * Reset
 ******************************************************************************/

void VM::Reset()
{
    mContext.Reset();
}

/******************************************************************************
 * Load Program
 ******************************************************************************/

bool VM::LoadProgram(const Program* program)
{
    if (program == nullptr)
    {
        return false;
    }

    mProgram = program;

    Reset();

    return true;
}

/******************************************************************************
 * Is Running
 ******************************************************************************/

bool VM::IsRunning() const
{
    if (mProgram == nullptr)
    {
        return false;
    }

    return mContext.mRunning;
}

/******************************************************************************
 * Program Counter
 ******************************************************************************/

uint16_t VM::GetProgramCounter() const
{
    return mContext.mProgramCounter;
}

/******************************************************************************
 * Execute One Instruction
 ******************************************************************************/

void VM::Step()
{
    if (!IsRunning())
    {
        return;
    }

    if (mContext.mProgramCounter >= mProgram->mInstructionCount)
    {
        mContext.mRunning = false;
        return;
    }

    const Instruction& instruction =
        mProgram->mInstructions[mContext.mProgramCounter];

    ExecuteInstruction(instruction);
}

/******************************************************************************
 * Instruction Decoder
 ******************************************************************************/

void VM::ExecuteInstruction(const Instruction& instruction)
{
    switch (instruction.opcode)
    {
        case Opcode::Nop:
        {
            mContext.mProgramCounter++;
            break;
        }

        case Opcode::LoadConst:
        {
            mContext.mVariables[instruction.p1] = instruction.p2;

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::LoadVar:
        {
            mContext.mRegister0 =
                mContext.mVariables[instruction.p1];

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::Forward:
        {
            RobotAPI::Forward(
                mContext.mVariables[instruction.p1]);

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::Backward:
        {
            RobotAPI::Backward(
                mContext.mVariables[instruction.p1]);

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::TurnLeft:
        {
            RobotAPI::TurnLeft(
                mContext.mVariables[instruction.p1]);

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::TurnRight:
        {
            RobotAPI::TurnRight(
                mContext.mVariables[instruction.p1]);

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::Stop:
        {
            RobotAPI::Stop();

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::Wait:
        {
            RobotAPI::Wait(
                instruction.p1);

            mContext.mProgramCounter++;

            break;
        }

        case Opcode::JumpIfTrue:
        {
            if (mContext.mVariables[instruction.p1] != 0)
            {
                mContext.mProgramCounter = instruction.p2;
            }
            else
            {
                mContext.mProgramCounter++;
            }

            break;
        }
        default:
        {
            /*
             * Unsupported opcode.
             */

            mContext.mRunning = false;

            break;
        }
    }
}