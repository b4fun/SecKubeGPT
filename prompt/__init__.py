from ._types import SpecResult, SecurityCheckProgram, CheckPayload
from ._pss import PodSecurityStandard
from ._expert import SecurityExpert

import typing as t

supported_programs = [
    PodSecurityStandard(),
    SecurityExpert(),
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
