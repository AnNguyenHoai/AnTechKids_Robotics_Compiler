#include "VM.h"
#include "../Robot/RobotAPI.h"
#include "generated/opcode.h"

VM::VM() : mProgram(nullptr) {}

void VM::Reset() { mContext.Reset(); }

bool VM::LoadProgram(const Program* program)
{
    if (program == nullptr) return false;
    mProgram = program;
    Reset();
    return true;
}

bool VM::IsRunning() const
{
    if (mProgram == nullptr) return false;
    return mContext.mRunning;
}

uint16_t VM::GetProgramCounter() const
{
    return mContext.mProgramCounter;
}

void VM::Step()
{
    if (!IsRunning()) return;
    if (mContext.mProgramCounter >= mProgram->mInstructionCount)
    {
        mContext.mRunning = false;
        return;
    }
    const Instruction& instruction = mProgram->mInstructions[mContext.mProgramCounter];
    ExecuteInstruction(instruction);
}

void VM::ExecuteInstruction(const Instruction& instruction)
{
    switch (instruction.opcode)
    {
        case Opcode::LoadConst:
            mContext.mVariables[instruction.p1] = instruction.p2;
            mContext.mProgramCounter++;
            break;

        case Opcode::LoadVar:
            mContext.mRegister0 = mContext.mVariables[instruction.p1];
            mContext.mProgramCounter++;
            break;

        case Opcode::Forward:
            RobotAPI::Forward(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::Backward:
            RobotAPI::Backward(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::TurnLeft:
            RobotAPI::TurnLeft(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::TurnRight:
            RobotAPI::TurnRight(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::Stop:
            RobotAPI::Stop();
            mContext.mProgramCounter++;
            break;

        case Opcode::Wait:
            RobotAPI::Wait(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::CompareEQ:
            mContext.mVariables[instruction.p3] =
                (mContext.mVariables[instruction.p1] == mContext.mVariables[instruction.p2]) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::CompareNE:
            mContext.mVariables[instruction.p3] =
                (mContext.mVariables[instruction.p1] != mContext.mVariables[instruction.p2]) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::CompareLT:
            mContext.mVariables[instruction.p3] =
                (mContext.mVariables[instruction.p1] < mContext.mVariables[instruction.p2]) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::CompareLE:
            mContext.mVariables[instruction.p3] =
                (mContext.mVariables[instruction.p1] <= mContext.mVariables[instruction.p2]) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::CompareGT:
            mContext.mVariables[instruction.p3] =
                (mContext.mVariables[instruction.p1] > mContext.mVariables[instruction.p2]) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::CompareGE:
            mContext.mVariables[instruction.p3] =
                (mContext.mVariables[instruction.p1] >= mContext.mVariables[instruction.p2]) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::Jump:
            mContext.mProgramCounter = instruction.p1;
            break;

        case Opcode::JumpIfFalse:
            if (mContext.mVariables[instruction.p1] == 0)
                mContext.mProgramCounter = instruction.p2;
            else
                mContext.mProgramCounter++;
            break;

        case Opcode::JumpIfTrue:
            if (mContext.mVariables[instruction.p1] != 0)
                mContext.mProgramCounter = instruction.p2;
            else
                mContext.mProgramCounter++;
            break;

        // --- Arithmetic operations ---
        case Opcode::Add:
            mContext.mVariables[instruction.p3] =
                mContext.mVariables[instruction.p1] + mContext.mVariables[instruction.p2];
            mContext.mProgramCounter++;
            break;

        case Opcode::Sub:
            mContext.mVariables[instruction.p3] =
                mContext.mVariables[instruction.p1] - mContext.mVariables[instruction.p2];
            mContext.mProgramCounter++;
            break;

        case Opcode::Mul:
            mContext.mVariables[instruction.p3] =
                mContext.mVariables[instruction.p1] * mContext.mVariables[instruction.p2];
            mContext.mProgramCounter++;
            break;

        case Opcode::Div:
            if (mContext.mVariables[instruction.p2] == 0)
                mContext.mVariables[instruction.p3] = 0;
            else
                mContext.mVariables[instruction.p3] =
                    mContext.mVariables[instruction.p1] / mContext.mVariables[instruction.p2];
            mContext.mProgramCounter++;
            break;

        case Opcode::Mod:
            if (mContext.mVariables[instruction.p2] == 0)
                mContext.mVariables[instruction.p3] = 0;
            else
                mContext.mVariables[instruction.p3] =
                    mContext.mVariables[instruction.p1] % mContext.mVariables[instruction.p2];
            mContext.mProgramCounter++;
            break;

        case Opcode::Pow:
        {
            int16_t base = mContext.mVariables[instruction.p1];
            int16_t exp = mContext.mVariables[instruction.p2];
            int32_t result = 1;
            for (int16_t i = 0; i < exp; ++i) {
                result *= base;
            }
            mContext.mVariables[instruction.p3] = (int16_t)result;
            mContext.mProgramCounter++;
            break;
        }

        case Opcode::Neg:
            mContext.mVariables[instruction.p3] = -mContext.mVariables[instruction.p1];
            mContext.mProgramCounter++;
            break;

        default:
            mContext.mRunning = false;
            break;
    }
}