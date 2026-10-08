import ast
from pathlib import Path
from .trace_channel_normalizer import RoboSimTraceChannelNormalizer
from .transformer import RoboSimTransformer


def rewrite(source_path: Path, output_path: Path, target: str = "robosim") -> None:
    """
    Read RoboSim source, transform to Standard Robot API, and write to output.

    target is used only for target-specific representation adapters such as
    the RoboSim 7-channel -> ESP32 Line5 projection.
    """
    with open(source_path, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    tree = RoboSimTraceChannelNormalizer(target=target).visit(tree)
    tree = RoboSimTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ast.unparse(tree))
