
---

### 2. `robot-docs/language/LANGUAGE_PIPELINE.md`

```markdown
# Language Build Pipeline

**Version:** 1.0  
**Status:** Architecture Freeze  
**Date:** 2026-08-09

## Overview

The Language Build Pipeline transforms the master language definition (`api.yaml`) into all required artifacts for the Robot Development Platform.

This pipeline is deterministic, repeatable, and produces consistent output across all environments.

---

## Pipeline Diagram
┌─────────────────────────────────────────────────────────────────────┐
│ LANGUAGE BUILD PIPELINE │
├─────────────────────────────────────────────────────────────────────┤
│ │
│ 1. LOAD │
│ api.yaml ─────────────────────────────────────────────────┐ │
│ │ │ │
│ ▼ │ │
│ 2. VALIDATE │ │
│ ┌──────────────────────┐ │ │
│ │ Syntax Validator │ │ │
│ │ Duplicate Validator │ │ │
│ │ Reference Validator │ │ │
│ │ Semantic Validator │ │ │
│ └──────────────────────┘ │ │
│ │ │ │
│ ▼ │ │
│ 3. GENERATE │ │
│ ┌───────────────────────────────────────────────────┐ │ │
│ │ OpcodeGenerator → opcode.py, opcode.h │ │ │
│ │ RegistryGenerator → function_registry.py │ │ │
│ │ RegistryJsonGenerator → registry.json │ │ │
│ │ SDKGenerator → robot/*.py │ │ │
│ │ DocGenerator → *.md │ │ │
│ └───────────────────────────────────────────────────┘ │ │
│ │ │ │
│ ▼ │ │
│ 4. INSTALL │ │
│ ┌───────────────────────────────────────────────────┐ │ │
│ │ Copy to robot-compiler/compiler/generated/ │ │ │
│ │ Copy to robot-platform/main/include/generated/ │ │ │
│ │ Copy to robot-frontend-robosim/robot/ │ │ │
│ │ Copy to robot-docs/generated/ │ │ │
│ └───────────────────────────────────────────────────┘ │ │
│ │ │ │
│ ▼ │ │
│ 5. VERIFY │ │
│ ┌───────────────────────────────────────────────────┐ │ │
│ │ Compile compiler tests │ │ │
│ │ Run compatibility tests │ │ │
│ │ Verify generated documentation │ │ │
│ └───────────────────────────────────────────────────┘ │ │
│ │
└─────────────────────────────────────────────────────────────────────┘

text

---

## Stage 1: Load

**Input:** `api.yaml`  
**Output:** `RobotLanguage` model object

```python
from language import LanguageLoader
language = LanguageLoader.load("specification/api.yaml")
Responsibility: Read YAML file, validate syntax, build internal model.

Failure: Exit with error if file missing or invalid YAML.

Stage 2: Validate
2.1 Syntax Validator
Checks YAML structure

Ensures required fields exist

Validates data types

2.2 Duplicate Validator
No duplicate function names

No duplicate opcode IDs

No duplicate category names

No duplicate opcode names

2.3 Reference Validator
All opcode IDs referenced

All handlers exist

All modules exist

2.4 Semantic Validator
Semantic classification valid

Priority levels valid

Argument counts match

Failure: Stop generation if any validator fails.

Stage 3: Generate
3.1 OpcodeGenerator
Outputs:

opcode.py – Python IntEnum for compiler

opcode.h – C++ enum for VM

python
class OpcodeGenerator(BaseGenerator):
    def generate(self, context):
        for func in context.query.functions():
            yield opcode_class
3.2 RegistryGenerator
Outputs:

function_registry.py – Python dispatch table for compiler

python
class RegistryGenerator(BaseGenerator):
    def generate(self, context):
        for func in context.query.functions():
            registry[func.name] = {
                "handler": handler,
                "opcode": opcode,
                "semantic": semantic,
                "priority": priority,
                "arguments": arg_count
            }
3.3 RegistryJsonGenerator
Outputs:

registry.json – JSON version for tooling

3.4 SDKGenerator
Outputs:

robot/*.py – Python SDK stubs

python
class SDKGenerator(BaseGenerator):
    def generate(self, context):
        for category in context.query.categories():
            generate_module(f"{category}.py")
3.5 DocGenerator
Outputs:

opcode_reference.md

language_reference.md

sdk_reference.md

robotapi_reference.md

Stage 4: Install
Destination Map
Artifact	Source	Destination
opcode.py	generated/opcode.py	robot-compiler/compiler/generated/
opcode.h	generated/opcode.h	robot-platform/main/include/generated/
opcode.json	generated/opcode.json	robot-platform/main/include/generated/
function_registry.py	generated/function_registry.py	robot-compiler/compiler/generated/
registry.json	generated/registry.json	robot-language/generated/
robot/*.py	robot/	robot-frontend-robosim/robot/
*.md	docs/generated/	robot-docs/generated/
Stage 5: Verify
5.1 Compiler Tests
bash
cd robot-compiler
python tests/run_tests.py
5.2 Compatibility Tests
bash
cd tests/compatibility
python runner.py
5.3 Documentation Verification
Ensure all generated docs exist

Ensure all links are valid

Quick Start
Full Build
bash
cd robot-language
python build.py
python install.py
cd ..
Validate Only
bash
cd robot-language
python validate.py
Generate Only
bash
cd robot-language
python build.py --no-validate
Pipeline Configuration
build.py
python
from build import Builder
from generators import *
from validation import *

builder = Builder()
builder.register_validator(DuplicateValidator())
builder.register_validator(SemanticValidator())
builder.register_validator(ReferenceValidator())

builder.register(OpcodeGenerator())
builder.register(OpcodeHeaderGenerator())
builder.register(OpcodeJsonGenerator())
builder.register(RegistryGenerator())
builder.register(RegistryJsonGenerator())
builder.register(SDKGenerator())
builder.register(DocGenerator())

builder.build()
Failure Modes
Failure	Action
Invalid YAML	Stop, report line/column
Duplicate function	Stop, report duplicate
Invalid semantic	Stop, report invalid value
Generator exception	Stop, report traceback
Install permission denied	Stop, report path
Conclusion
The Language Build Pipeline provides a deterministic, repeatable process for generating all language artifacts from a single source of truth. Every developer can now reliably produce consistent artifacts across all environments.