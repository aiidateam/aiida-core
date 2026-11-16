###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared flaky collaborator for the graph-vs-restart evaluation.

Both evaluation arms (``BaseRestartWorkChain`` and direct ``GraphIR``) wrap
this child process. Agents must NOT modify this file; the hidden acceptance
tests import the same fixture.
"""

from __future__ import annotations

from aiida import orm
from aiida.engine import WorkChain, calcfunction

__all__ = ('FlakyChild',)


@calcfunction
def _attempt_outputs(attempt: orm.Int) -> dict:
    """Derive attempt outputs with CREATE provenance.

    A workflow cannot create `Data` (its outputs must be existing nodes linked
    with RETURN), so the new `Int` values are built here and returned unchanged
    by :class:`FlakyChild`.
    """
    value = attempt.value
    return {'result': orm.Int(value * 10), 'next_attempt': orm.Int(value + 1)}


class FlakyChild(WorkChain):
    """Deterministic flaky child: transient failures, then success, or fatal abort.

    Behaviour of :meth:`evaluate`:

    * if ``fatal`` is true, return exit code 420 (``ERROR_FATAL``);
    * else if ``attempt <= fail_until``, return exit code 410 (``ERROR_TRANSIENT``);
    * else expose ``result = attempt * 10`` and finish with exit status 0.

    ``next_attempt`` (``attempt + 1``) is always exposed so wrappers can advance
    their retry counter from child outputs if they wish.

    Provenance: workflows may only RETURN existing nodes, so the new ``Int``
    values are created by the :func:`_attempt_outputs` calcfunction (CREATE)
    and returned unchanged by the workflow.
    """

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        """Define the process spec."""
        super().define(spec)
        spec.input('attempt', valid_type=orm.Int, help='One-based attempt counter supplied by the wrapper.')
        spec.input('fail_until', valid_type=orm.Int, default=lambda: orm.Int(2))
        spec.input('fatal', valid_type=orm.Bool, default=lambda: orm.Bool(False))
        spec.output('result', valid_type=orm.Int, required=False)
        spec.output('next_attempt', valid_type=orm.Int)
        spec.exit_code(410, 'ERROR_TRANSIENT', message='Simulated transient failure.')
        spec.exit_code(420, 'ERROR_FATAL', message='Simulated permanent failure.')
        spec.outline(cls.evaluate)

    def evaluate(self):  # type: ignore[no-untyped-def]
        """Evaluate one attempt."""
        derived = _attempt_outputs(self.inputs.attempt)
        self.out('next_attempt', derived['next_attempt'])
        if self.inputs.fatal.value:
            return self.exit_codes.ERROR_FATAL
        if self.inputs.attempt.value <= self.inputs.fail_until.value:
            return self.exit_codes.ERROR_TRANSIENT
        self.out('result', derived['result'])
