# Control Instruction Package

This package implements the control flow instructions for the Robot VM.

## Instructions

| Instruction | Opcode | Operands | Description |
|-------------|--------|----------|-------------|
| `JUMP` | JUMP | target (int) | Unconditional jump to target address |
| `JUMP_IF_TRUE` | JUMP_IF_TRUE | condition (bool), target (int) | Jump if condition is true |
| `JUMP_IF_FALSE` | JUMP_IF_FALSE | condition (bool), target (int) | Jump if condition is false |
| `COMPARE_EQ` | COMPARE_EQ | left, right | Compare equal; pushes boolean |
| `COMPARE_NE` | COMPARE_NE | left, right | Compare not equal; pushes boolean |
| `COMPARE_LT` | COMPARE_LT | left, right | Compare less than; pushes boolean |
| `COMPARE_LE` | COMPARE_LE | left, right | Compare less or equal; pushes boolean |
| `COMPARE_GT` | COMPARE_GT | left, right | Compare greater than; pushes boolean |
| `COMPARE_GE` | COMPARE_GE | left, right | Compare greater or equal; pushes boolean |
| `RETURN` | RETURN | none | Return from function, restore call stack and PC |

## Execution Semantics

All control instructions operate purely within the VM; they do not access RobotAPI or HAL.

- **JUMP**: Sets the program counter to the target address.
- **JUMP_IF_TRUE/FALSE**: Pops condition and target from operand stack. If condition matches, jumps; otherwise advances PC.
- **COMPARE_***: Pops two values from operand stack, performs comparison, pushes boolean result.
- **RETURN**: Pops a stack frame, restores return address and PC.

## Operand Stack Usage

- JUMP: `[target]` → `[]` (PC updated)
- JUMP_IF_TRUE: `[condition, target]` → `[]` (PC updated or advanced)
- JUMP_IF_FALSE: `[condition, target]` → `[]`
- COMPARE_*: `[left, right]` → `[result]` (boolean)
- RETURN: `[]` → `[]` (PC restored from frame)

## Validation

Each instruction validates operand count and types. Invalid targets are caught by the VM.

## Dependencies

- `ExecutionContext` (for PC, stack, call stack)
- No RobotAPI, no HAL, no hardware.

## Testing

End-to-end tests cover:
- Simple jump
- Conditional branches
- Nested branches
- Loops
- Function return
- Invalid target handling