# Language Development Guide

**Version:** 1.0  
**Status:** Architecture Freeze  
**Date:** 2026-08-09

## Overview

This guide provides step-by-step instructions for developing and maintaining the Robot Language System. All developers working on language features must follow these guidelines.

---

## Quick Reference

### Adding a New API

```bash
# 1. Edit api.yaml
vim robot-language/specification/api.yaml

# 2. Build artifacts
cd robot-language
python build.py
python install.py
cd ..

# 3. Implement handler
vim robot-compiler/compiler/handlers/appropriate_handler.py

# 4. Add rewrite rule (if needed)
vim robot-frontend-robosim/frontend/transformer.py

# 5. Add test
vim tests/compatibility/test_new_api.py

# 6. Run tests
python run_all_tests.py
Modifying an Existing API
bash
# 1. Edit api.yaml
vim robot-language/specification/api.yaml

# 2. Build artifacts
cd robot-language
python build.py
python install.py
cd ..

# 3. Update handler (if needed)
vim robot-compiler/compiler/handlers/appropriate_handler.py

# 4. Run tests
python run_all_tests.py
Removing an API
bash
# 1. Remove from api.yaml
vim robot-language/specification/api.yaml

# 2. Build artifacts
cd robot-language
python build.py
python install.py
cd ..

# 3. Remove handler
rm robot-compiler/compiler/handlers/handler_api.py

# 4. Remove tests
rm tests/compatibility/test_removed_api.py

# 5. Run tests
python run_all_tests.py
Detailed Steps
Step 1: Edit api.yaml
Location: robot-language/specification/api.yaml

Adding a function:

yaml
- name: new_function
  opcode: NewFunction
  opcode_id: 100
  semantic: Native
  priority: P1
  description: Does something useful
  args:
    - name: param1
      type: int
    - name: param2
      type: string
  returns: int
Modifying a function:

Update description, semantic, priority, etc.

Change args list

Update returns

Removing a function:

Delete the entire entry

Step 2: Build Artifacts
bash
cd robot-language
python build.py
Expected output:

text
============================================================
Robot Language Build
============================================================

Running Duplicate Validator...
PASS

Running Semantic Validator...
PASS

Running Reference Validator...
PASS

Running Opcode Generator...
PASS

Running Registry Generator...
PASS

Running SDK Generator...
PASS

Running Documentation Generator...
PASS

============================================================
Build Summary
============================================================

Categories : 10
Functions  : 45
Opcodes    : 45
Public     : 33
Internal   : 12
Validators : 3
Generators : 7

============================================================
BUILD SUCCESS
============================================================
Step 3: Install Artifacts
bash
python install.py
Expected output:

text
Copy to compiler: opcode.py
Copy to compiler: function_registry.py
Copy to platform: opcode.h
Copy to platform: opcode.json
Copy to docs: opcode_reference.md
Copy to docs: language_reference.md
Copy to docs: sdk_reference.md
Copy to docs: robotapi_reference.md
Copied SDK to robot-frontend-robosim/robot/
Artifacts installed.
Step 4: Implement Handler
Location: robot-compiler/compiler/handlers/

python
class AppropriateHandler:
    @staticmethod
    def new_function(compiler, node):
        """Handle new_function API call."""
        compiler.validate_argument_count(node, "new_function", 2)
        param1 = compiler.resolve_argument(node.args[0])
        param2 = compiler.resolve_argument(node.args[1])
        # Generate bytecode
        compiler.program.emit(Opcode.NewFunction.value, param1, param2, 0)
Step 5: Add Rewrite Rule
Location: robot-frontend-robosim/frontend/transformer.py

python
# In visit_Expr method
if (isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "NewFunction"
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "rcu"):
    return self._handle_simple_call(node.value, "new_function", 2)
Step 6: Add Test
Location: tests/compatibility/test_new_function.py

python
def test_new_function():
    code = "rcu.NewFunction(1, 2)"
    assert compile_api(code) is True
Step 7: Run Tests
bash
python run_all_tests.py
Expected: All tests PASS

Generator Development
Creating a New Generator
Create generator class:

python
# robot-language/generators/my_generator.py
from .base_generator import BaseGenerator

class MyGenerator(BaseGenerator):
    name = "My Generator"
    
    def generate(self, context):
        # Read from context.query
        # Generate artifacts
        pass
Register in build.py:

python
# robot-language/build.py
from generators.my_generator import MyGenerator
builder.register(MyGenerator())
Install generated files:

python
# robot-language/install.py
for file in SOURCE.glob("my_output.*"):
    shutil.copy2(file, DEST_COMPILER / file.name)
Validation Development
Creating a New Validator
Create validator class:

python
# robot-language/validation/my_validator.py
from .base_validator import BaseValidator
from language.exceptions import ValidationError

class MyValidator(BaseValidator):
    name = "My Validator"
    
    def validate(self, query):
        for func in query.functions():
            # Check something
            if invalid:
                raise ValidationError("Invalid something")
Register in build.py:

python
# robot-language/build.py
from validation.my_validator import MyValidator
builder.register_validator(MyValidator())
Common Tasks
Changing an Opcode ID
Edit api.yaml – update opcode_id

Run build – regenerates all artifacts

Update VM – if new ID conflicts

Run tests – verify all pass

Changing a Semantic Classification
Edit api.yaml – update semantic

Run build – regenerates registry

Update handler behavior – if semantic changed

Run tests – verify all pass

Adding a New Category
Edit api.yaml – add new category

Create handler module – in handlers/

Run build – regenerates artifacts

Add tests – for new category

Troubleshooting
Build Fails: Duplicate Function
Error:

text
Duplicate Function: my_function
Solution: Remove duplicate from api.yaml

Build Fails: Invalid Semantic
Error:

text
Invalid Semantic: MySemantic
Solution: Use valid semantic: Native, Rewrite, NOP, Stub, Approximation, Dummy

Compiler Fails: Unknown Opcode
Error:

text
Unknown opcode: NewFunction
Solution: Run python build.py and python install.py in robot-language/

Tests Fail: API Not Recognized
Error:

text
Unknown function 'new_function'
Solution:

Check api.yaml – function exists?

Run python build.py – artifacts generated?

Run python install.py – artifacts installed?

Check handler – implemented?

Best Practices
Do
✅ Always run build after changing api.yaml

✅ Always run tests before committing

✅ Keep handlers simple and focused

✅ Document semantic choices in api.yaml

✅ Use consistent naming conventions

Don't
❌ Edit generated files

❌ Hardcode API metadata in compiler

❌ Skip validation on build

❌ Forget to add tests for new APIs

❌ Mix semantic changes with other changes

Conclusion
Following this guide ensures consistent, reliable language development. All language changes flow through the same pipeline, producing predictable results across the entire platform.