# Language Architecture

**Version:** 1.0  
**Status:** Architecture Freeze  
**Date:** 2026-08-09

## Overview

The Robot Language System is the foundation of the Robot Development Platform. It defines the language syntax, semantics, and all API contracts. Every component of the platform derives from this single language definition.

---

## Philosophy

### Single Source of Truth
There shall be ONE authoritative language definition.
Everything else is generated from it.

text

### Separation of Concerns

- **Language Definition** – What the language is
- **Language Implementation** – How the language is compiled
- **Language Runtime** – How the language executes

### Generated Code First

- Generated code is always current
- No manual synchronization
- No out-of-date documentation

---

## Architecture Layers
┌─────────────────────────────────────────────────────────────────┐
│ LANGUAGE DEFINITION LAYER │
├─────────────────────────────────────────────────────────────────┤
│ api.yaml │
│ • Language name and version │
│ • All categories and functions │
│ • Semantic classification │
│ • Priority levels │
│ • Opcode mapping │
│ • Argument signatures │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ VALIDATION LAYER │
├─────────────────────────────────────────────────────────────────┤
│ Validators │
│ • Syntax │
│ • Duplicate │
│ • Reference │
│ • Semantic │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ GENERATION LAYER │
├─────────────────────────────────────────────────────────────────┤
│ Generators │
│ • OpcodeGenerator → opcode.py, opcode.h │
│ • RegistryGenerator → function_registry.py │
│ • SDKGenerator → robot/*.py │
│ • DocGenerator → *.md │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ INSTALLATION LAYER │
├─────────────────────────────────────────────────────────────────┤
│ Installer │
│ • Copy to compiler │
│ • Copy to platform │
│ • Copy to frontend │
│ • Copy to docs │
└─────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────┐
│ CONSUMER LAYER │
├─────────────────────────────────────────────────────────────────┤
│ Compiler │
│ Runtime (VM) │
│ Frontend (RoboSim) │
│ Documentation │
│ RoboStudio │
│ Tooling │
└─────────────────────────────────────────────────────────────────┘

text

---

## Language Definition (`api.yaml`)

### Structure

```yaml
language:
  name: Robot Language
  version: 1.0.0

categories:
  category_name:
    description: Category description
    module: handler_module
    handler: HandlerClass
    functions:
      - name: function_name
        opcode: OpcodeName
        opcode_id: 42
        semantic: Native | Rewrite | NOP | Stub | Approximation | Dummy
        priority: P0 | P1 | P2 | P3
        description: Function description
        args:
          - name: arg_name
            type: int | float | string | bool | any
        returns: int | float | string | bool | void
Semantic Meanings
Semantic	Description
Native	Implemented exactly as specified
Rewrite	Transformed by frontend into native operations
NOP	Compile only, no runtime operation
Stub	Compile passes, runtime placeholder
Approximation	Implemented with equivalent behavior
Dummy	Returns fixed, deterministic value
Priority Levels
Priority	Meaning
P0	Critical – Core compatibility
P1	Important – High impact
P2	Optional – Medium impact
P3	Future – Low impact
Validation Pipeline
1. Syntax Validator
python
def validate_syntax(data):
    # Validate YAML structure
    # Check required fields
    # Validate data types
2. Duplicate Validator
python
def validate_duplicates(query):
    # Check duplicate function names
    # Check duplicate opcode IDs
    # Check duplicate opcode names
    # Check duplicate categories
3. Reference Validator
python
def validate_references(query):
    # Check all handlers exist
    # Check all modules exist
    # Check all opcode IDs referenced
4. Semantic Validator
python
def validate_semantic(query):
    # Check semantic values valid
    # Check priority values valid
    # Check argument counts match
Generator Architecture
Base Generator
python
class BaseGenerator(ABC):
    name: str = "Generator"
    
    @abstractmethod
    def generate(self, context: BuildContext) -> None:
        """Generate artifacts from language definition."""
        pass
Generator Registry
python
generators = [
    OpcodeGenerator(),
    OpcodeHeaderGenerator(),
    OpcodeJsonGenerator(),
    RegistryGenerator(),
    RegistryJsonGenerator(),
    SDKGenerator(),
    DocGenerator(),
]
Build Context
python
class BuildContext:
    root: Path
    spec_path: Path
    language: RobotLanguage
    query: LanguageQuery
    generated_dir: Path
    sdk_dir: Path
    docs_dir: Path
Artifact Ownership
Artifact	Generator	Consumer
opcode.py	OpcodeGenerator	Compiler
opcode.h	OpcodeHeaderGenerator	Platform/VM
opcode.json	OpcodeJsonGenerator	Tooling
function_registry.py	RegistryGenerator	Compiler
registry.json	RegistryJsonGenerator	Tooling
robot/*.py	SDKGenerator	Frontend/Users
docs/*.md	DocGenerator	Documentation
Extension Strategy
Adding a New API
Edit api.yaml

yaml
- name: new_api
  opcode: NewApi
  opcode_id: 100
  semantic: Native
  priority: P1
  description: New API description
  args:
    - name: param
      type: int
Run build

bash
cd robot-language && python build.py && python install.py
Implement handler

python
# compiler/handlers/appropriate_handler.py
@staticmethod
def new_api(compiler, node):
    param = compiler.resolve_argument(node.args[0])
    compiler.program.emit(Opcode.NewApi.value, param, 0, 0)
Add rewrite rule (if needed)

python
# frontend/transformer.py
if attr == "NewApi":
    return self._handle_simple_call(node, "new_api", 1)
Add test

python
# tests/compatibility/test_new_api.py
def test_new_api():
    compile_api("new_api(1)")
Developer Rules
Do:
✅ Edit api.yaml when adding/modifying language features

✅ Run build.py and install.py after changes

✅ Implement handlers in handlers/ directory

✅ Add tests for new features

Don't:
❌ Edit generated files in generated/

❌ Hardcode API metadata in compiler

❌ Duplicate API definitions across files

❌ Manually sync artifacts

Conclusion
The Robot Language Architecture provides a unified, extensible foundation for the entire Robot Development Platform. All components derive from a single language definition, ensuring consistency and reducing maintenance overhead.