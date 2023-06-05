from ._types import SpecResult, SecurityCheckProgram, CheckPayload
from . import _pss, _expert

import typing as t

supported_programs = [
    _pss.create_program(),
    _expert.create_program(),
]


def check(
    programs: t.List[SecurityCheckProgram], payload: CheckPayload
) -> t.List[SpecResult]:
    """Run the security check programs on the given spec.

    Args:
        programs: List of programs to run.
        payload: The security check payload.

    Returns:
        A list of security check results.
    """
    rv = []
    for program in programs:
        rv.append(program.check(payload))

    return rv


__all__ = [
    "SpecResult",
    "SecurityCheckProgram",
    "CheckPayload",
    "supported_programs",
    "check",
]
