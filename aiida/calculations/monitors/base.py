# -*- coding: utf-8 -*-
"""Monitors for the :class:`aiida.calculations.arithmetic.add.ArithmeticAddCalculation` plugin."""
from __future__ import annotations

import tempfile

from aiida.orm import CalcJobNode
from aiida.transports import Transport


def always_kill(node: CalcJobNode, transport: Transport) -> str | None:  # pylint: disable=unused-argument
    """Retrieve and inspect files in working directory of job to determine whether the job should be killed.

    This particular implementation is just for demonstration purposes and will kill the job as long as there is a
    submission script that contains some content, which should always be the case.

    :param node: The node representing the calculation job.
    :param transport: The transport that can be used to retrieve files from remote working directory.
    :returns: A string if the job should be killed, `None` otherwise.
    """
    with tempfile.NamedTemporaryFile('w+') as handle:
        transport.getfile('_aiidasubmit.sh', handle.name)
        handle.seek(0)
        output = handle.read()

    if output:
        return 'Detected a non-empty submission script'

    return None
