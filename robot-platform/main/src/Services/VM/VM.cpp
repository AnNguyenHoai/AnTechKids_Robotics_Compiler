#include "VM.h"
#include "CooperativeLineOperation.h"
#include "../Robot/RobotAPI.h"
#include "../../../include/generated/opcode.h"
#include <Arduino.h>

// Instruction tracing is disabled in production by default. Tight forever
// loops must not flood Serial and starve the cooperative runtime. Developers
// can enable it explicitly at build time with -DVM_TRACE_ENABLED=1.
#ifndef VM_TRACE_ENABLED
#define VM_TRACE_ENABLED 0
#endif

namespace {
constexpr uint16_t POW_MULTIPLIES_PER_STEP = 8;
}

VM::VM() : mProgram(nullptr) {}

void VM::CancelPendingOperation(bool stopLineMotors)
{
    // Preserve the existing fail-safe line cleanup even if the pending marker
    // was already cleared by a malformed/legacy path.
    CooperativeLineOperation::Cancel(stopLineMotors);

    if (mContext.mPendingOperation == VMPendingOperation::Mp3Play) {
        RobotAPI::EndMp3PlayCooperative();
    }

    mContext.ClearPendingOperation();
}

void VM::Reset() {
    CancelPendingOperation(true);
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

const char* VM::GetErrorId() const
{
    return VMErrorId(static_cast<VMErrorCode>(mContext.mErrorCode));
}

const char* VM::GetErrorMessage() const
{
    return VMErrorMessage(static_cast<VMErrorCode>(mContext.mErrorCode));
}

// ---- DIAGNOSTIC: manual control ----
void VM::SetRunning(bool running) {
    if (!running) {
        CancelPendingOperation(true);
    }
    mContext.mRunning = running;
}

void VM::Start() {
    CancelPendingOperation(true);
    mContext.mRunning = true;
    mContext.mProgramCounter = 0;
    mContext.mErrorCode = ToErrorCode(VMErrorCode::None);
    // Do not reset variables; they are already loaded
    // But we can reset any other state if needed
}

void VM::Step()
{
    if (!IsRunning()) return;

    // If the program has ended, stop normally and tear down any cooperative
    // operation that might have been left active by a malformed program.
    if (mContext.mProgramCounter >= mProgram->mInstructionCount)
    {
        CancelPendingOperation(true);
        mContext.mRunning = false;
        mContext.mErrorCode = ToErrorCode(VMErrorCode::None);
        return;
    }

    const Instruction& instruction = mProgram->mInstructions[mContext.mProgramCounter];

#if VM_TRACE_ENABLED
    Serial.printf("[TRACE] PC=%03d | Opcode=%d\n", mContext.mProgramCounter, (uint8_t)instruction.opcode);
#endif

    ExecuteInstruction(instruction);

    // Stop on a real VM error and release any pending cooperative actuator.
    if (mContext.mErrorCode != ToErrorCode(VMErrorCode::None)) {
        CancelPendingOperation(true);
        mContext.mRunning = false;
        Serial.printf("[VM] Error code: %d (%s)\n", mContext.mErrorCode, GetErrorId());
    }
}

bool VM::ContinuePendingLineOperation()
{
    if (mContext.mPendingOperation != VMPendingOperation::Line) {
        return false;
    }

    if (!CooperativeLineOperation::Update()) {
        mContext.ClearPendingOperation();
        mContext.mProgramCounter++;
    }
    return true;
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
            CooperativeLineOperation::Cancel(false);
            RobotAPI::Stop();
            mContext.mProgramCounter++;
            break;

        case Opcode::Wait:
        {
            const int32_t requestedMs = mContext.mVariables[instruction.p1];

            if (mContext.mPendingOperation == VMPendingOperation::None) {
                if (requestedMs <= 0) {
                    mContext.mProgramCounter++;
                    break;
                }
                mContext.mPendingOperation = VMPendingOperation::Wait;
                mContext.mPendingDeadlineMs = millis() + static_cast<uint32_t>(requestedMs);
                break;
            }

            if (mContext.mPendingOperation == VMPendingOperation::Wait &&
                mContext.IsPendingDeadlineReached(millis())) {
                mContext.ClearPendingOperation();
                mContext.mProgramCounter++;
            }
            break;
        }

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
                mContext.mRunning = false;
                mContext.mErrorCode = ToErrorCode(VMErrorCode::InvalidJump);
            }
            else if (target == mProgram->mInstructionCount) {
                mContext.mRunning = false;
                mContext.mErrorCode = ToErrorCode(VMErrorCode::None);
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
                    mContext.mRunning = false;
                    mContext.mErrorCode = ToErrorCode(VMErrorCode::InvalidJump);
                }
                else if (target == mProgram->mInstructionCount) {
                    mContext.mRunning = false;
                    mContext.mErrorCode = ToErrorCode(VMErrorCode::None);
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
                    mContext.mRunning = false;
                    mContext.mErrorCode = ToErrorCode(VMErrorCode::InvalidJump);
                }
                else if (target == mProgram->mInstructionCount) {
                    mContext.mRunning = false;
                    mContext.mErrorCode = ToErrorCode(VMErrorCode::None);
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
                mContext.mErrorCode = ToErrorCode(VMErrorCode::DivisionByZero);
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
                mContext.mErrorCode = ToErrorCode(VMErrorCode::ModuloByZero);
                mContext.mRunning = false;
            } else {
                mContext.mVariables[instruction.p3] =
                    mContext.mVariables[instruction.p1] % mContext.mVariables[instruction.p2];
                mContext.mProgramCounter++;
            }
            break;

        case Opcode::Pow:
        {
            if (mContext.mPendingOperation == VMPendingOperation::None) {
                const int16_t base = static_cast<int16_t>(mContext.mVariables[instruction.p1]);
                const int16_t exp = static_cast<int16_t>(mContext.mVariables[instruction.p2]);

                // Preserve legacy semantics: zero/negative exponents execute no
                // multiplications and therefore produce 1 immediately.
                if (exp <= 0) {
                    mContext.mVariables[instruction.p3] = 1;
                    mContext.mProgramCounter++;
                    break;
                }

                mContext.mPendingPowBase = base;
                mContext.mPendingPowRemaining = static_cast<uint16_t>(exp);
                mContext.mPendingPowResult = 1;
                mContext.mPendingOperation = VMPendingOperation::Pow;
            }

            if (mContext.mPendingOperation == VMPendingOperation::Pow) {
                uint16_t multiplies = 0;
                while (mContext.mPendingPowRemaining > 0 &&
                       multiplies < POW_MULTIPLIES_PER_STEP) {
                    // Keep the exact legacy repeated-multiply ordering. This
                    // changes scheduling only: long exponents yield across
                    // bounded Step() calls instead of monopolizing one Step().
                    mContext.mPendingPowResult *= mContext.mPendingPowBase;
                    --mContext.mPendingPowRemaining;
                    ++multiplies;
                }

                if (mContext.mPendingPowRemaining == 0) {
                    const int16_t result = static_cast<int16_t>(mContext.mPendingPowResult);
                    mContext.ClearPendingOperation();
                    mContext.mVariables[instruction.p3] = result;
                    mContext.mProgramCounter++;
                }
            }
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
                mContext.mErrorCode = ToErrorCode(VMErrorCode::StackOverflow);
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
                mContext.mErrorCode = ToErrorCode(VMErrorCode::InvalidReturn);
            }
            break;

        case Opcode::ReadUltrasonic: {
            int16_t value = RobotAPI::ReadUltrasonic();
            mContext.mVariables[instruction.p1] = value;
            Serial.printf("[VM-ULTRA-DIAG] PC=%u p1=%d value=%d\\n",
                          mContext.mProgramCounter,
                          instruction.p1,
                          value);
            mContext.mProgramCounter++;
            break;
        }

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
            if (ContinuePendingLineOperation()) {
                break;
            }
            if (CooperativeLineOperation::StartIntersectionStop(
                    mContext.mVariables[instruction.p1],
                    mContext.mVariables[instruction.p2])) {
                mContext.mPendingOperation = VMPendingOperation::Line;
            } else {
                mContext.mProgramCounter++;
            }
            break;

        case Opcode::SetMp3Play:
        {
            if (mContext.mPendingOperation == VMPendingOperation::None) {
                const uint32_t durationMs = RobotAPI::BeginMp3PlayCooperative(
                    mContext.mVariables[instruction.p1]);
                if (durationMs == 0) {
                    mContext.mProgramCounter++;
                    break;
                }

                mContext.mPendingOperation = VMPendingOperation::Mp3Play;
                mContext.mPendingDeadlineMs = millis() + durationMs;
                break;
            }

            if (mContext.mPendingOperation == VMPendingOperation::Mp3Play &&
                mContext.IsPendingDeadlineReached(millis())) {
                RobotAPI::EndMp3PlayCooperative();
                mContext.ClearPendingOperation();
                mContext.mProgramCounter++;
            }
            break;
        }

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

        case Opcode::LineMillisecond:
            if (ContinuePendingLineOperation()) {
                break;
            }
            if (CooperativeLineOperation::StartMillisecond(
                    mContext.mVariables[instruction.p1],
                    mContext.mVariables[instruction.p2])) {
                mContext.mPendingOperation = VMPendingOperation::Line;
            } else {
                mContext.mProgramCounter++;
            }
            break;

        case Opcode::LineStop:
            CooperativeLineOperation::Cancel(false);
            RobotAPI::LineStop();
            mContext.mProgramCounter++;
            break;

        case Opcode::LineTurnEncounterLine:
            if (ContinuePendingLineOperation()) {
                break;
            }
            if (CooperativeLineOperation::StartTurnEncounterLine(
                    mContext.mVariables[instruction.p1],
                    mContext.mVariables[instruction.p2],
                    mContext.mVariables[instruction.p3])) {
                mContext.mPendingOperation = VMPendingOperation::Line;
            } else {
                mContext.mProgramCounter++;
            }
            break;

        case Opcode::LineForBmp:
            if (ContinuePendingLineOperation()) {
                break;
            }
            if (CooperativeLineOperation::StartBmp(
                    mContext.mVariables[instruction.p1],
                    mContext.mVariables[instruction.p2])) {
                mContext.mPendingOperation = VMPendingOperation::Line;
            } else {
                mContext.mProgramCounter++;
            }
            break;

        default:
            mContext.mRunning = false;
            mContext.mErrorCode = ToErrorCode(VMErrorCode::InvalidOpcode);
            break;
    }
}
