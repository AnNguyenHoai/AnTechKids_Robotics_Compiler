# integration/end_to_end/benchmark.py
import time
import sys
import json
from pathlib import Path
import statistics

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
COMPILER_ROOT = REPO_ROOT / "robot-compiler"
FRONTEND_ROOT = REPO_ROOT / "robot-frontend-robosim"

if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from frontend.compiler import RoboSimCompiler
from compiler.binary import ProgramEncoder, BinarySerializer
from runtime import ProgramLoader, VirtualMachine
from runtime.hardware import MockHardware
from compiler.generated.opcode import Opcode
from compiler.isa import ISAProgram, ISAFunction, ISAInstruction, ISAOperand

PROGRAMS_DIR = Path(__file__).parent / "programs"
RESULTS_FILE = Path(__file__).parent / "benchmark_results.json"

def convert_instruction(ins):
    """Convert compiler.Instruction to ISAInstruction."""
    opcode = Opcode(ins.opcode)
    operands = []
    
    if opcode == Opcode.LoadConst:
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.Forward, Opcode.Backward, Opcode.TurnLeft, Opcode.TurnRight, Opcode.Wait):
        operands.append(ISAOperand.integer(ins.p1))
    elif opcode == Opcode.Stop:
        pass
    elif opcode == Opcode.Jump:
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.JumpIfFalse, Opcode.JumpIfTrue):
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode in (Opcode.Add, Opcode.Sub, Opcode.Mul, Opcode.Div, Opcode.Mod, Opcode.Pow):
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
        operands.append(ISAOperand.integer(ins.p3))
    elif opcode == Opcode.Neg:
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p3))
    elif opcode == Opcode.Store:
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
    elif opcode == Opcode.Call:
        operands.append(ISAOperand.integer(ins.p1))
    elif opcode == Opcode.Return:
        pass
    elif opcode in (Opcode.CompareEQ, Opcode.CompareNE, Opcode.CompareLT, 
                    Opcode.CompareLE, Opcode.CompareGT, Opcode.CompareGE):
        operands.append(ISAOperand.integer(ins.p1))
        operands.append(ISAOperand.integer(ins.p2))
        operands.append(ISAOperand.integer(ins.p3))
    elif opcode == Opcode.Label:
        pass
    else:
        if ins.p1 != 0: operands.append(ISAOperand.integer(ins.p1))
        if ins.p2 != 0: operands.append(ISAOperand.integer(ins.p2))
        if ins.p3 != 0: operands.append(ISAOperand.integer(ins.p3))
    
    return ISAInstruction(opcode, operands)

def benchmark_program(program_path, iterations=5):
    compiler = RoboSimCompiler()
    
    compile_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        program = compiler.compile(program_path)
        compile_times.append(time.perf_counter() - start)
    
    isa_prog = ISAProgram()
    func = ISAFunction("main")
    for ins in program.instructions:
        func.add_instruction(convert_instruction(ins))
    isa_prog.add_function(func)
    
    instruction_count = len(program.instructions)
    
    encoder = ProgramEncoder()
    start = time.perf_counter()
    binary_prog = encoder.encode(isa_prog)
    encode_time = time.perf_counter() - start
    
    serializer = BinarySerializer()
    start = time.perf_counter()
    binary_data = serializer.serialize(binary_prog)
    serialize_time = time.perf_counter() - start
    
    loader = ProgramLoader()
    load_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        runtime_prog = loader.load(binary_prog)
        load_times.append(time.perf_counter() - start)
    
    hardware = MockHardware()
    vm = VirtualMachine(hardware=hardware)
    vm.load(runtime_prog)
    start = time.perf_counter()
    vm.run()
    execution_time = time.perf_counter() - start
    
    memory_usage = sys.getsizeof(binary_data) + sys.getsizeof(runtime_prog)
    
    return {
        "program": str(program_path.name),
        "instruction_count": instruction_count,
        "compile_time_avg": statistics.mean(compile_times),
        "compile_time_min": min(compile_times),
        "compile_time_max": max(compile_times),
        "encode_time": encode_time,
        "serialize_time": serialize_time,
        "load_time_avg": statistics.mean(load_times),
        "load_time_min": min(load_times),
        "load_time_max": max(load_times),
        "execution_time": execution_time,
        "memory_usage_bytes": memory_usage,
    }

def main():
    results = []
    for prog_path in PROGRAMS_DIR.glob("*.py"):
        print(f"Benchmarking {prog_path.name}...")
        try:
            result = benchmark_program(prog_path)
            results.append(result)
            print(f"  Instructions: {result['instruction_count']}")
            print(f"  Compile avg: {result['compile_time_avg']*1000:.2f} ms")
            print(f"  Load avg:    {result['load_time_avg']*1000:.2f} ms")
            print(f"  Execute:     {result['execution_time']*1000:.2f} ms")
            print()
        except Exception as e:
            print(f"  FAILED: {e}")
    
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()