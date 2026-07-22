import json
from pathlib import Path
from .base_generator import BaseGenerator


class DocGenerator(BaseGenerator):
    name = "Documentation Generator"

    def generate(self, context):
        query = context.query
        docs_dir = context.root / "docs"
        generated_docs = docs_dir / "generated"
        generated_docs.mkdir(parents=True, exist_ok=True)

        self._generate_opcode_reference(query, generated_docs)
        self._generate_language_reference(query, generated_docs)
        self._generate_sdk_reference(query, generated_docs)
        self._generate_robotapi_reference(query, generated_docs)

        print(f"[DocGenerator] Generated documentation in {generated_docs}")

    def _generate_opcode_reference(self, query, output_dir):
        lines = [
            "# Opcode Reference",
            "",
            "This is a complete list of all opcodes used by the Robot VM.",
            "",
            "| Opcode | ID | Category | Description |",
            "|--------|----|----------|-------------|"
        ]
        for cat_name, _, func in query.functions():
            opcode = query.opcode_of(func)
            opcode_id = query.opcode_id_of(func)
            desc = query.description_of(func)
            lines.append(f"| `{opcode}` | {opcode_id} | {cat_name} | {desc} |")

        lines.append("")
        lines.append("---")
        lines.append("**Note:** Internal opcodes (ID >= 8) are used by the compiler and VM internally, not exposed to users.")
        lines.append("")

        with open(output_dir / "opcode_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_language_reference(self, query, output_dir):
        lines = [
            "# Robot Language Reference",
            "",
            f"**Language:** {query.name}",
            f"**Version:** {query.version}",
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

        for cat_name, cat in query.categories().items():
            if cat_name == "internal":
                continue
            for func in cat.get("functions", []):
                args = ", ".join(arg["name"] for arg in query.arguments_of(func))
                desc = query.description_of(func)
                lines.append(f"| `{func['name']}({args})` | {query.argument_count_of(func)} | {desc} |")

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

    def _generate_sdk_reference(self, query, output_dir):
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
        for cat_name, cat in query.categories().items():
            if cat_name == "internal":
                continue
            lines.append(f"### {cat_name.capitalize()}")
            for func in cat.get("functions", []):
                args = ", ".join(arg["name"] for arg in query.arguments_of(func))
                desc = query.description_of(func)
                lines.append(f"#### `{func['name']}({args})`")
                lines.append(f"- {desc}")
                lines.append("")

        with open(output_dir / "sdk_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _generate_robotapi_reference(self, query, output_dir):
        lines = [
            "# RobotAPI Reference (C++)",
            "",
            "The RobotAPI is the hardware abstraction layer. All robot hardware access goes through this API.",
            "",
            "## Functions",
            ""
        ]
        for cat_name, cat in query.categories().items():
            if cat_name == "internal":
                continue
            lines.append(f"### {cat_name.capitalize()}")
            for func in cat.get("functions", []):
                arg_str = ", ".join(f"{arg['type']} {arg['name']}" for arg in query.arguments_of(func))
                desc = query.description_of(func)
                lines.append(f"#### `void {func['name']}({arg_str})`")
                lines.append(f"- {desc}")
                lines.append("")

        lines.append("")
        lines.append("## Implementation")
        lines.append("The RobotAPI is implemented in `robot-platform/main/src/Services/Robot/RobotAPI.cpp`.")
        lines.append("It maps VM calls to hardware drivers (Motors, Sensors, etc.).")
        lines.append("")

        with open(output_dir / "robotapi_reference.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))