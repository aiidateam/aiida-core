###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Shared failure vocabulary for restartable graphs.

`RestartErrors` plays the role of `BaseRestartWorkChain.spec` exit codes:
one place naming the failures the restart machinery itself reports, so
handlers and combinators share the vocabulary instead of redeclaring it.
"""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum

__all__ = ('RestartErrors',)


class RestartErrors(ExitCodeEnum):
    """Failures reported by the restart machinery, not by the retried step."""

    SUB_PROCESS_EXCEPTED = ExitCode(301, 'The sub process excepted.')
    SUB_PROCESS_KILLED = ExitCode(302, 'The sub process was killed.')
    MAXIMUM_ITERATIONS_EXCEEDED = ExitCode(401, 'The maximum number of iterations was exceeded.')
    UNHANDLED_FAILURE = ExitCode(402, 'The process failed with an unhandled failure.')
