# runtime/tests/test_integration_esp32.py
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, ISAOperand
from compiler.binary import ProgramEncoder
from compiler.generated.opcode import Opcode
from runtime import ProgramLoader, VirtualMachine, ESP32Hardware, BoardConfiguration


def make_move_stop_program():
    """Create program: LoadConst(0,50); Forward(0); Stop()"""
    prog = ISAProgram()
    func = ISAFunction("main")
    # Load constant 50 into variable 0
    func.add_instruction(ISAInstruction(Opcode.LoadConst, [ISAOperand.integer(0), ISAOperand.integer(50)]))
    # Forward using variable 0
    func.add_instruction(ISAInstruction(Opcode.Forward, [ISAOperand.integer(0)]))
    # Stop
    func.add_instruction(ISAInstruction(Opcode.Stop, []))
    prog.add_function(func)
    return prog


def make_wait_program():
    """Create program: LoadConst(0,200); Wait(0); Stop()"""
    prog = ISAProgram()
    func = ISAFunction("main")
    # Load constant 200 into variable 0
    func.add_instruction(ISAInstruction(Opcode.LoadConst, [ISAOperand.integer(0), ISAOperand.integer(200)]))
    # Wait using variable 0
    func.add_instruction(ISAInstruction(Opcode.Wait, [ISAOperand.integer(0)]))
    # Stop
    func.add_instruction(ISAInstruction(Opcode.Stop, []))
    prog.add_function(func)
    return prog


class TestIntegrationESP32(unittest.TestCase):
    def setUp(self):
        self.config = BoardConfiguration(
            left_motor_pin=25,
            right_motor_pin=26,
            pwm_channel_left=0,
            pwm_channel_right=1,
        )

    def test_vm_with_esp32_hardware_movestop(self):
        hw = ESP32Hardware(self.config)
        vm = VirtualMachine(hardware=hw)
        isa_prog = make_move_stop_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm.load(runtime_prog)
        vm.run()
        self.assertEqual(vm.state.value, "finished")
        # After Forward(50) then Stop, motor should be 0
        self.assertEqual(hw.motor._last_left, 0)
        self.assertEqual(hw.motor._last_right, 0)

    def test_vm_with_esp32_hardware_wait(self):
        import time
        hw = ESP32Hardware(self.config)
        vm = VirtualMachine(hardware=hw)
        isa_prog = make_wait_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm.load(runtime_prog)
        start = time.time()
        vm.run()
        elapsed = time.time() - start
        self.assertAlmostEqual(elapsed, 0.2, places=1)
        self.assertEqual(vm.state.value, "finished")

    def test_vm_step_by_step(self):
        hw = ESP32Hardware(self.config)
        vm = VirtualMachine(hardware=hw)
        isa_prog = make_move_stop_program()
        encoder = ProgramEncoder()
        binary_prog = encoder.encode(isa_prog)
        loader = ProgramLoader()
        runtime_prog = loader.load(binary_prog)
        vm.load(runtime_prog)

        # Step 1: LoadConst 50 into v0
        vm.step()
        # Step 2: Forward using v0
        vm.step()
        self.assertEqual(hw.motor._last_left, 50)
        self.assertEqual(hw.motor._last_right, 50)

        # Step 3: Stop
        vm.step()
        self.assertEqual(hw.motor._last_left, 0)
        self.assertEqual(hw.motor._last_right, 0)

        # Step 4: end
        vm.step()
        self.assertEqual(vm.state.value, "finished")


if __name__ == "__main__":
    unittest.main()