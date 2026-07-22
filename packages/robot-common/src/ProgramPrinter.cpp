#include "ProgramPrinter.h"
#include "OpcodeRegistry.h"
#include <iomanip>

void ProgramPrinter::print(const Program& program, std::ostream& out) {
    size_t pc = 0;
    for (const auto& func : program.functions) {
        out << "Function: " << func.name << "\n";
        for (const auto& ins : func.instructions) {
            out << std::setw(4) << std::setfill('0') << pc++ << " ";
            out << OpcodeRegistry::instance().getName(ins.opcode);
            for (const auto& op : ins.operands) {
                out << " ";
                switch (op.getType()) {
                    case OperandType::Integer:
                        out << op.asInteger();
                        break;
                    case OperandType::Float:
                        out << op.asFloat();
                        break;
                    case OperandType::Boolean:
                        out << (op.asBoolean() ? "true" : "false");
                        break;
                    case OperandType::String:
                        out << "\"" << op.asString() << "\"";
                        break;
                    case OperandType::Variable:
                        out << "v" << op.asIndex();
                        break;
                    case OperandType::Label:
                        out << "L" << op.asIndex();
                        break;
                    case OperandType::Enum:
                        out << "e" << op.asIndex();
                        break;
                }
            }
            out << "\n";
        }
        out << "\n";
    }
}