###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution-facing contracts for codes used in calculation job scripts."""

import typing as t

from aiida.common.folders import Folder
from aiida.orm import Computer

__all__ = ('CodeExecutionProtocol',)


class CodeExecutionProtocol(t.Protocol):
    """Capabilities required to generate and validate a calculation job's code invocation.

    A code must separately be a stored ORM data node to participate in a CalcJob's provenance.
    """

    def can_run_on_computer(self, computer: Computer) -> bool: ...

    def validate_working_directory(self, folder: Folder) -> None: ...

    def get_prepend_cmdline_params(
        self, mpi_args: list[str] | None = None, extra_mpirun_params: list[str] | None = None
    ) -> list[str]: ...

    def get_executable_cmdline_params(self, cmdline_params: list[str] | None = None) -> list[str]: ...

    @property
    def with_mpi(self) -> bool | None: ...

    @property
    def prepend_text(self) -> str: ...

    @property
    def append_text(self) -> str: ...

    @property
    def use_double_quotes(self) -> bool: ...

    @property
    def wrap_cmdline_params(self) -> bool: ...
