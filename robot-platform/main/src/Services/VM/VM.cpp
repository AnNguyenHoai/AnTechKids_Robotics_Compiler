#include "VM.h"
#include "../Robot/RobotAPI.h"
#include "../../../include/generated/opcode.h"
#include <Arduino.h> 
// Bật trace để debug (có thể comment để tắt)
#define VM_TRACE_ENABLED 1

VM::VM() : mProgram(nullptr) {}

void VM::Reset() {
    mContext.Reset();
}

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

uint8_t VM::GetErrorCode() const
{
    return mContext.mErrorCode;
}

void VM::Step()
{
    if (!IsRunning()) return;

    // Nếu đã hết chương trình → dừng bình thường (không lỗi)
    if (mContext.mProgramCounter >= mProgram->mInstructionCount)
    {
        mContext.mRunning = false;
        mContext.mErrorCode = 0;   // <-- không báo lỗi
        return;
    }

    const Instruction& instruction = mProgram->mInstructions[mContext.mProgramCounter];

#ifdef VM_TRACE_ENABLED
    Serial.printf("[TRACE] PC=%03d | Opcode=%d\n", mContext.mProgramCounter, (uint8_t)instruction.opcode);
#endif

    ExecuteInstruction(instruction);

    // Nếu sau khi execute mà lỗi thực sự (khác 0) thì dừng
    if (mContext.mErrorCode != 0) {
        mContext.mRunning = false;
        Serial.printf("[VM] Error code: %d\n", mContext.mErrorCode);
    }
}
void VM::ExecuteInstruction(const Instruction& instruction)
{
    switch (instruction.opcode)
    {
        case Opcode::LoadConst:
            mContext.mVariables[instruction.p1] = instruction.p2;
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
        {
            uint16_t target = instruction.p2;

            if (target > mProgram->mInstructionCount) {
                // Target vượt quá END thật sự là invalid
                mContext.mRunning = false;
                mContext.mErrorCode = 3;
            }
            else if (target == mProgram->mInstructionCount) {
                // Jump tới END label = kết thúc chương trình bình thường
                mContext.mRunning = false;
                mContext.mErrorCode = 0;
            }
            else {
                mContext.mProgramCounter = target;
            }

            break;
        }

        case Opcode::JumpIfFalse:
        {
            if (mContext.mVariables[instruction.p1] == 0) {
                uint16_t target = instruction.p2;

                if (target > mProgram->mInstructionCount) {
                    // Invalid jump target
                    mContext.mRunning = false;
                    mContext.mErrorCode = 3;
                }
                else if (target == mProgram->mInstructionCount) {
                    // Jump to END = normal program termination
                    mContext.mRunning = false;
                    mContext.mErrorCode = 0;
                }
                else {
                    mContext.mProgramCounter = target;
                }
            }
            else {
                mContext.mProgramCounter++;
            }

            break;
        }

        case Opcode::JumpIfTrue:
        {
            if (mContext.mVariables[instruction.p1] != 0) {
                uint16_t target = instruction.p2;

                if (target > mProgram->mInstructionCount) {
                    // Invalid jump target
                    mContext.mRunning = false;
                    mContext.mErrorCode = 3;
                }
                else if (target == mProgram->mInstructionCount) {
                    // Jump to END = normal program termination
                    mContext.mRunning = false;
                    mContext.mErrorCode = 0;
                }
                else {
                    mContext.mProgramCounter = target;
                }
            }
            else {
                mContext.mProgramCounter++;
            }

            break;
        }

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
            if (mContext.mVariables[instruction.p2] == 0) {
                mContext.mVariables[instruction.p3] = 0;
                mContext.mErrorCode = 6; // Division by zero
                mContext.mRunning = false;
            } else {
                mContext.mVariables[instruction.p3] =
                    mContext.mVariables[instruction.p1] / mContext.mVariables[instruction.p2];
                mContext.mProgramCounter++;
            }
            break;

        case Opcode::Mod:
            if (mContext.mVariables[instruction.p2] == 0) {
                mContext.mVariables[instruction.p3] = 0;
                mContext.mErrorCode = 7; // Modulo by zero
                mContext.mRunning = false;
            } else {
                mContext.mVariables[instruction.p3] =
                    mContext.mVariables[instruction.p1] % mContext.mVariables[instruction.p2];
                mContext.mProgramCounter++;
            }
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

        case Opcode::Store:
            mContext.mVariables[instruction.p2] = mContext.mVariables[instruction.p1];
            mContext.mProgramCounter++;
            break;

        case Opcode::Call:
            mContext.mReturnAddress = mContext.mProgramCounter + 1;
            mContext.mFramePointer = mContext.mCallStackPointer;
            if (mContext.mCallStackPointer < MAX_CALL_STACK) {
                mContext.mCallStack[mContext.mCallStackPointer++] = mContext.mReturnAddress;
            } else {
                mContext.mRunning = false;
                mContext.mErrorCode = 4; // Stack overflow
                return;
            }
            mContext.mProgramCounter = instruction.p1;
            break;

        case Opcode::Return:
            if (mContext.mCallStackPointer > 0) {
                mContext.mCallStackPointer--;
                mContext.mProgramCounter = mContext.mCallStack[mContext.mCallStackPointer];
            } else {
                mContext.mRunning = false;
                mContext.mErrorCode = 5; // Return without call
            }
            break;
        case Opcode::ReadUltrasonic:
            mContext.mVariables[instruction.p1] = RobotAPI::ReadUltrasonic();
            mContext.mProgramCounter++;
            break;

        case Opcode::ReadTouch:
            mContext.mVariables[instruction.p2] = RobotAPI::ReadTouch(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::ReadLight:
            mContext.mVariables[instruction.p2] = RobotAPI::ReadLight(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::ReadColor:
            mContext.mVariables[instruction.p1] = RobotAPI::ReadColor();
            mContext.mProgramCounter++;
            break;

        case Opcode::ReadLine:
            mContext.mVariables[instruction.p2] = RobotAPI::ReadLine(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;
        case Opcode::SetMotorSpeed:
            RobotAPI::SetMotorSpeed(mContext.mVariables[instruction.p1],
                                    mContext.mVariables[instruction.p2]);
            mContext.mProgramCounter++;
            break;
        case Opcode::SetServo:
            RobotAPI::SetServo(mContext.mVariables[instruction.p1],
                               mContext.mVariables[instruction.p2]);
            mContext.mProgramCounter++;
            break;

        case Opcode::Set3CLed:
            RobotAPI::Set3CLed(mContext.mVariables[instruction.p1],
                               mContext.mVariables[instruction.p2]);
            mContext.mProgramCounter++;
            break;

        case Opcode::SetLightSensorLed:
            RobotAPI::SetLightSensorLed(mContext.mVariables[instruction.p1],
                                        mContext.mVariables[instruction.p2]);
            mContext.mProgramCounter++;
            break;

        case Opcode::SetMotorStraightAngle:
            RobotAPI::SetMotorStraightAngle(mContext.mVariables[instruction.p1],
                                            mContext.mVariables[instruction.p2],
                                            mContext.mVariables[instruction.p3],
                                            mContext.mVariables[instruction.p4]);
            mContext.mProgramCounter++;
            break;

        case Opcode::LineIntersectionStop:
            RobotAPI::LineIntersectionStop(mContext.mVariables[instruction.p1],
                                           mContext.mVariables[instruction.p2]);
            mContext.mProgramCounter++;
            break;
        case Opcode::SetMp3Play:
            RobotAPI::SetMp3Play(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;
        case Opcode::GetTraceValue:
            mContext.mVariables[instruction.p3] = RobotAPI::GetTraceValue(
                mContext.mVariables[instruction.p1],
                mContext.mVariables[instruction.p2]
            );
            mContext.mProgramCounter++;
            break;

        case Opcode::GetTraceState:
            mContext.mVariables[instruction.p3] = RobotAPI::GetTraceState(
                mContext.mVariables[instruction.p1],
                mContext.mVariables[instruction.p2]
            ) ? 1 : 0;
            mContext.mProgramCounter++;
            break;

        case Opcode::GetTraceRaw:
            mContext.mVariables[instruction.p3] = RobotAPI::GetTraceRaw(
                mContext.mVariables[instruction.p1]
            );
            mContext.mProgramCounter++;
            break;
        case Opcode::LineBasis:
            RobotAPI::LineBasis(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::LineFollow:
            RobotAPI::LineFollow(mContext.mVariables[instruction.p1]);
            mContext.mProgramCounter++;
            break;

        case Opcode::LineStop:
            RobotAPI::LineStop();
            mContext.mProgramCounter++;
            break;
        default:
            mContext.mRunning = false;
            mContext.mErrorCode = 1; // Invalid opcode
            break;
    }
}