# Portable Python Fixture Boundary

The RSD-20-P positive fixture stages a real CPython interpreter, its core DLLs, and the standard library needed by the clean-machine probe. It deliberately does not copy the optional Windows `DLLs` directory because the probe does not import those extension modules. This keeps the fixture dependency-closed while preserving the production proof's fail-closed PE dependency scanning.
