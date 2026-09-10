###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Workgraph process implementations."""

from __future__ import annotations

from typing_extensions import override

from aiida.engine.processes.process import Process

__all__ = ('WorkGraphProcess',)


class WorkGraphProcess(Process):
    """Minimal process stand-in for a future workgraph engine.

    The scheduler only admits or holds this process. Future workgraph
    orchestration belongs here, optionally delegated to a composed helper.
    """

    @override
    async def run(self) -> None:
        """Finish immediately until workgraph orchestration is implemented."""
