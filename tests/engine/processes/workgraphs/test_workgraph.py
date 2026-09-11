###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the workgraph-process stand-in."""

from __future__ import annotations

from aiida.engine import WorkGraphProcess
from aiida.engine.processes.persistence import InMemoryCheckpointPersister
from aiida.engine.processes.process import Process


def test_has_process_pid_and_checkpoint(aiida_localhost):
    """Test the stand-in has normal process persistence and a database pid."""
    process = WorkGraphProcess()
    persister = InMemoryCheckpointPersister()
    persister.save_checkpoint(process)

    restored = persister.load_checkpoint(process.pid).decode()

    assert isinstance(process, Process)
    assert process.pid == process.node.pk
    assert isinstance(restored, WorkGraphProcess)
    assert restored.pid == process.pid
