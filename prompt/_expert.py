import pathlib

from ._types import SpecResult, CheckPayload, SecurityCheckProgram
from ._spec import SpecProgram

source_dir = pathlib.Path(__file__).parent
with open(source_dir / "_expert.yaml") as f:
    _yaml_spec = f.read()


class Program(SpecProgram):
    def create_succeed_result(
        self, payload: CheckPayload, response_content: str
    ) -> SpecResult:
        message = "🙌  expert gave a full pass on your input!"
        if payload.model.startswith("gpt-3.5"):
            message = "🙌  expert gave a full pass on your input, you may want to validate again with a more powerful model like GPT-4 ."
        return self.succeed(response_content, message)


def create_program() -> SecurityCheckProgram:
    return Program.from_yaml_spec(_yaml_spec)
