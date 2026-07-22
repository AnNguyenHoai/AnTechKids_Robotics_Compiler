import json
from pathlib import Path
from .base_generator import BaseGenerator


class DocGenerator(BaseGenerator):
    name = "Documentation Generator"

    def generate(self, context):
        language = context.language
        docs_dir = context.root / "docs"   # robot-docs
        generated_docs = docs_dir / "generated"
        generated_docs.mkdir(parents=True, exist_ok=True)

        # 1. Opcode Reference
        self._generate_opcode_reference(language, generated_docs)

        # 2. Language Reference (từ spec và mô tả)
        self._generate_language_reference(language, generated_docs)

        # 3. SDK Reference (từ các function)
        self._generate_sdk_reference(language, generated_docs)

        # 4. RobotAPI Reference (dành cho C++)
        self._generate_robotapi_reference(language, generated_docs)

        print(f"[DocGenerator] Generated documentation in {generated_docs}")

    def _generate_opcode_reference(self, language, output_dir):
        """Sinh file opcode_reference.md"""
        lines = [
            "# Opcode Reference",
            "",
            "This is a complete list of all opcodes used by the Robot VM.",
            "",
            "| Opcode | ID | Category | Description |",
            "|--------|----|----------|-------------|"
        ]
        for _, _, func in language.all_functions():
            opcode = func["opcode"]
            opcode_id = func["opcode_id"]
            category = func.get("category", "unknown")
            desc = func.get("description", "")
            lines.append(f"| `{opcode}` | {opcode_id} | {category} | {desc} |")

        lines.append("")
        lines.append("---")
        lines.append("**Note:** Internal opcodes (ID >= 8) are used by the compiler and VM internally, not exposed to users.")
        lines.append("")

        with open(output_dir / "opcode_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_language_reference(self, language, output_dir):
        """Sinh file language_reference.md (tổng quan ngôn ngữ)"""
        lines = [
            "# Robot Language Reference",
            "",
            f"**Language:** {language.name}",
            f"**Version:** {language.version}",
            "",
            "## Overview",
            "Robot Language is a simple, Python-like language for programming robots. It compiles to bytecode and runs on the Robot VM.",
            "",
            "## Syntax",
            "",
            "### Variables",
            "```python",
            "speed = 80",
            "```",
            "",
            "### Functions (built-in)",
            "Robot Language provides several built-in functions:",
            "| Function | Arguments | Description |",
            "|----------|-----------|-------------|"
        ]

        for category_name, category in language.categories.items():
            if category_name == "internal":
                continue
            for func in category["functions"]:
                args = ", ".join(arg["name"] for arg in func["args"])
                lines.append(f"| `{func['name']}({args})` | {len(func['args'])} | {func.get('description', '')} |")

        lines.append("")
        lines.append("### User-Defined Functions")
        lines.append("```python")
        lines.append("def my_function(param1, param2):")
        lines.append("    # function body")
        lines.append("    return value")
        lines.append("```")
        lines.append("")
        lines.append("### Control Flow")
        lines.append("- `if condition:` ... `else:` ...")
        lines.append("- `while condition:` ...")
        lines.append("- `break` and `continue`")
        lines.append("")
        lines.append("### Scope Rules")
        lines.append("- Variables defined outside functions are global.")
        lines.append("- Variables defined inside functions are local.")
        lines.append("- Local variables shadow globals.")
        lines.append("")
        lines.append("---")
        lines.append("*For a complete specification, see `api.yaml`*.")

        with open(output_dir / "language_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_sdk_reference(self, language, output_dir):
        """Sinh file sdk_reference.md (từ spec)"""
        lines = [
            "# SDK Reference (Python)",
            "",
            "This document describes the Python SDK generated from the specification.",
            "",
            "## Installation",
            "The SDK is automatically installed as part of the `robot-language` build.",
            "",
            "## API Reference",
            ""
        ]
        for category_name, category in language.categories.items():
            if category_name == "internal":
                continue
            lines.append(f"### {category_name.capitalize()}")
            for func in category["functions"]:
                args = ", ".join(arg["name"] for arg in func["args"])
                desc = func.get("description", "")
                lines.append(f"#### `{func['name']}({args})`")
                lines.append(f"- {desc}")
                lines.append("")

        with open(output_dir / "sdk_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_robotapi_reference(self, language, output_dir):
        """Sinh file robotapi_reference.md (cho C++ RobotAPI)"""
        lines = [
            "# RobotAPI Reference (C++)",
            "",
            "The RobotAPI is the hardware abstraction layer. All robot hardware access goes through this API.",
            "",
            "## Functions",
            ""
        ]
        for category_name, category in language.categories.items():
            if category_name == "internal":
                continue
            lines.append(f"### {category_name.capitalize()}")
            for func in category["functions"]:
                args = ", ".join(f"{arg['type']} {arg['name']}" for arg in func["args"])
                desc = func.get("description", "")
                lines.append(f"#### `void {func['name']}({args})`")
                lines.append(f"- {desc}")
                lines.append("")

        lines.append("")
        lines.append("## Implementation")
        lines.append("The RobotAPI is implemented in `robot-platform/main/src/Services/Robot/RobotAPI.cpp`.")
        lines.append("It maps VM calls to hardware drivers (Motors, Sensors, etc.).")
        lines.append("")

        with open(output_dir / "robotapi_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))