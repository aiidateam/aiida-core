"""Monitors for the :class:`aiida.calculations.arithmetic.add.ArithmeticAddCalculation` plugin."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from aiida.orm import CalcJobNode
from aiida.transports import Transport


def always_kill(node: CalcJobNode, transport: Transport) -> str | None:
    """Retrieve and inspect files in working directory of job to determine whether the job should be killed.

    This particular implementation is just for demonstration purposes and will kill the job as long as there is a
    submission script that contains some content, which should always be the case.

    :param node: The node representing the calculation job.
    :param transport: The transport that can be used to retrieve files from remote working directory.
    :returns: A string if the job should be killed, `None` otherwise.
    """
    cwd = node.get_remote_workdir()
    if cwd is None:
        raise ValueError('The remote work directory cannot be None')

    with tempfile.NamedTemporaryFile('w+', delete=False) as handle:
        temp_path = handle.name

    try:
        transport.getfile(str(Path(cwd).joinpath('_aiidasubmit.sh')), temp_path)
        with open(temp_path, 'r') as handle:
            output = handle.read()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    if output:
        return 'Detected a non-empty submission script'

    return None
