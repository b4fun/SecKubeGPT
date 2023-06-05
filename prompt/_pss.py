from ._types import SecurityCheckProgram
from ._spec import SpecProgram
import pathlib

source_dir = pathlib.Path(__file__).parent
with open(source_dir / "_pss.yaml") as f:
    _yaml_spec = f.read()


def create_program() -> SecurityCheckProgram:
    return SpecProgram.from_yaml_spec(_yaml_spec)
