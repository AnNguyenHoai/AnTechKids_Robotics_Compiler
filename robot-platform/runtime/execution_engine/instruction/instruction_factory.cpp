#include "instruction_factory.h"
#include "unknown_instruction_handler.h"
#include "nop_handler.h"
#include "end_handler.h"
#include "wait_handler.h"
#include "jump_handler.h"
#include "jump_if_handler.h"
#include "load_const_handler.h"
#include "store_handler.h"
#include "load_handler.h"
#include "return_handler.h"
#include "motion/move_instruction.h"
#include "motion/stop_instruction.h"
#include "motion/turn_instruction.h"
#include "motion/speed_instruction.h"
#include "execution_types.h"
#include <unordered_map>
#include <memory>
#include "control/jump_instruction.h"
#include "control/jump_if_true_instruction.h"
#include "control/jump_if_false_instruction.h"
#include "control/compare_instruction.h"
#include "control/return_instruction.h"
#include "sensor/ultrasonic_instruction.h"
#include "sensor/line_sensor_instruction.h"
#include "sensor/light_sensor_instruction.h"
#include "sensor/touch_sensor_instruction.h"
#include "sensor/color_sensor_instruction.h"



namespace robot {
namespace execution {

class DefaultInstructionFactory : public InstructionFactory {
public:
    DefaultInstructionFactory() {
        // Core instructions
        registerHandler(static_cast<uint32_t>(Opcode::NOP), []() { return std::make_unique<NopHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::END), []() { return std::make_unique<EndHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::WAIT), []() { return std::make_unique<WaitHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::JUMP), []() { return std::make_unique<JumpHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::JUMP_IF), []() { return std::make_unique<JumpIfHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::LOAD_CONST), []() { return std::make_unique<LoadConstHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::STORE), []() { return std::make_unique<StoreHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::LOAD), []() { return std::make_unique<LoadHandler>(); });
        registerHandler(static_cast<uint32_t>(Opcode::RETURN), []() { return std::make_unique<ReturnHandler>(); });

        // Motion instructions
        registerHandler(static_cast<uint32_t>(Opcode::FORWARD), []() { return std::make_unique<motion::MoveInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::BACKWARD), []() { return std::make_unique<motion::MoveInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::TURN_LEFT), []() { return std::make_unique<motion::MoveInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::TURN_RIGHT), []() { return std::make_unique<motion::MoveInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::STOP), []() { return std::make_unique<motion::StopInstruction>(); });
        // Note: TurnInstruction is not yet used as a separate handler; we use MoveInstruction for turns.
        // But we could add TurnInstruction for explicit turn opcode if needed.
        // For now, we map TURN_LEFT/RIGHT to MoveInstruction as well.
        registerHandler(static_cast<uint32_t>(Opcode::SET_SPEED), []() { return std::make_unique<motion::SpeedInstruction>(); });
        // Control instructions
        registerHandler(static_cast<uint32_t>(Opcode::JUMP), []() { return std::make_unique<control::JumpInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::JUMP_IF_TRUE), []() { return std::make_unique<control::JumpIfTrueInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::JUMP_IF_FALSE), []() { return std::make_unique<control::JumpIfFalseInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::COMPARE_EQ), []() { return std::make_unique<control::CompareInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::COMPARE_NE), []() { return std::make_unique<control::CompareInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::COMPARE_LT), []() { return std::make_unique<control::CompareInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::COMPARE_LE), []() { return std::make_unique<control::CompareInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::COMPARE_GT), []() { return std::make_unique<control::CompareInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::COMPARE_GE), []() { return std::make_unique<control::CompareInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::RETURN), []() { return std::make_unique<control::ReturnInstruction>(); });
        // Trong constructor:
        registerHandler(static_cast<uint32_t>(Opcode::ReadUltrasonic), []() { return std::make_unique<sensor::UltrasonicInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::ReadLine), []() { return std::make_unique<sensor::LineSensorInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::ReadLight), []() { return std::make_unique<sensor::LightSensorInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::ReadTouch), []() { return std::make_unique<sensor::TouchSensorInstruction>(); });
        registerHandler(static_cast<uint32_t>(Opcode::ReadColor), []() { return std::make_unique<sensor::ColorSensorInstruction>(); });    

        
    }

    std::unique_ptr<InstructionHandler> createHandler(uint32_t opcode) const override {
        auto it = m_handlers.find(opcode);
        if (it != m_handlers.end()) {
            return it->second();
        }
        return std::make_unique<UnknownInstructionHandler>(opcode);
    }

private:
    using Creator = std::unique_ptr<InstructionHandler> (*)();
    std::unordered_map<uint32_t, Creator> m_handlers;

    void registerHandler(uint32_t opcode, Creator creator) {
        m_handlers[opcode] = creator;
    }
};

std::unique_ptr<InstructionFactory> InstructionFactory::defaultFactory() {
    return std::make_unique<DefaultInstructionFactory>();
}

} // namespace execution
} // namespace robot