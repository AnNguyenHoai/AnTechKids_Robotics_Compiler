import ast
from pathlib import Path
from ..ir import IRProgram, IRPrinter
from .parser import Parser
from .visitor import ASTVisitor
from .errors import CompilerError
from ..passes import PassContext, PassManager
from ..validation import ValidationPass
from ..canonicalization import CanonicalizationPass
from ..lowering import LoweringPass
from ..diagnostics import DiagnosticEngine


class FrontendCompiler:
    def compile(self, source_path: Path) -> IRProgram:
        # 1. Parse
        tree = Parser.parse(source_path)

        # 2. Generate IR
        visitor = ASTVisitor(source_path)
        visitor.visit(tree)
        program = visitor.compile()

        # 3. Create PassContext with diagnostics
        diag = DiagnosticEngine()
        context = PassContext(program, diag)

        # 4. Setup pass manager and run passes
        manager = PassManager()
        manager.register(ValidationPass())
        manager.register(CanonicalizationPass())
        manager.register(LoweringPass())

        result = manager.run(context)

        # 5. Report diagnostics
        if diag.diagnostics:
            diag.print_all()

        if not result.success:
            raise CompilerError("Compilation failed due to errors")

        return program