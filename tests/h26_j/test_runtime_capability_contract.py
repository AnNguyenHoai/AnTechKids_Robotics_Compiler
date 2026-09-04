import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

from compiler.binary import ProgramEncoder
from compiler.generated.opcode import Opcode
from compiler.isa import ISAFunction, ISAInstruction, ISAOperand, ISAProgram
from runtime.capability_contract import CapabilityContractError, capability_ids_for_opcodes
from runtime.loader import ProgramLoader
from runtime.program import RuntimeProgram
from runtime.instruction import RuntimeInstruction
from runtime.vm import VirtualMachine


class RuntimeCapabilityContractTests(unittest.TestCase):
    def make_binary(self, *instructions):
        program = ISAProgram()
        function = ISAFunction("main")
        for instruction in instructions:
            function.add_instruction(instruction)
        program.add_function(function)
        return ProgramEncoder().encode(program)

    def test_opcode_requirements_are_derived_from_canonical_model(self):
        required = capability_ids_for_opcodes([Opcode.Forward.value, Opcode.SetServo.value])
        self.assertEqual(required, ("motion.basic", "actuator.servo"))

    def test_loader_attaches_required_capabilities_to_runtime_program(self):
        binary = self.make_binary(ISAInstruction(Opcode.Forward, [ISAOperand.integer(0)]))
        runtime_program = ProgramLoader.load(binary)
        self.assertEqual(runtime_program.required_capabilities, ("motion.basic",))

    def test_runtime_rejects_missing_capability_before_execution(self):
        program = RuntimeProgram(constants=[], functions=[], instructions=[RuntimeInstruction(Opcode.SetServo, [], 0)], required_capabilities=("actuator.servo",))
        vm = VirtualMachine(runtime_capabilities={"motion.basic", "runtime.control"})
        with self.assertRaisesRegex(CapabilityContractError, "actuator.servo"):
            vm.load(program)
        self.assertEqual(vm.get_state().name, "CREATED")

    def test_runtime_accepts_program_when_all_capabilities_are_present(self):
        program = RuntimeProgram(constants=[], functions=[], instructions=[RuntimeInstruction(Opcode.Nop, [], 0)], required_capabilities=("runtime.control",))
        vm = VirtualMachine(runtime_capabilities={"runtime.control"})
        vm.load(program)
        self.assertEqual(vm.get_state().name, "LOADED")

    def test_existing_runtime_callers_remain_backward_compatible(self):
        program = RuntimeProgram(constants=[], functions=[], instructions=[])
        vm = VirtualMachine()
        vm.load(program)
        self.assertEqual(vm.get_state().name, "LOADED")

    def test_flat_instruction_stream_falls_back_when_entry_function_is_absent(self):
        """Function metadata without entry 0 must not break legacy flat programs."""
        helper = ISAFunction("helper")
        helper.function_id = 1
        program = RuntimeProgram(
            constants=[],
            functions=[helper],
            instructions=[RuntimeInstruction(Opcode.Nop, [], 0)],
            entry_function_id=0,
        )
        vm = VirtualMachine()
        vm.load(program)
        self.assertEqual(vm.get_state().name, "LOADED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
