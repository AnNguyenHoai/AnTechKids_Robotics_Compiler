# H31 Boolean Expression Completeness Tests

Run:

```powershell
python tests/h31_boolean/run_h31_boolean.py
```

The gate covers:

- `and`, `or`, `not` truthiness
- normalized Boolean results (`0` / `1`)
- left-to-right short-circuit
- nested arithmetic and Boolean operands
- Python AST precedence for `not` > `and` > `or`
- assignment, `if`, `while`, and API-argument expression contexts
- preservation of H29-C scope boundaries such as chained-comparison rejection

The gate intentionally uses only the existing canonical Boolean-control opcodes; H31 does not add or renumber ISA opcodes.
