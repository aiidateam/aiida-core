# -*- coding: utf-8 -*-
"""AiiDA specific implementation of plumpy's ProcessSpec."""
import plumpy
from aiida.work.ports import InputPort, PortNamespace


ExitCode = namedtuple('ExitCode', 'status message')


class ProcessSpec(plumpy.ProcessSpec):
    """
    Sub classes plumpy.ProcessSpec to define the INPUT_PORT_TYPE and PORT_NAMESPACE_TYPE
    with the variants implemented in AiiDA
    """

    INPUT_PORT_TYPE = InputPort
    PORT_NAMESPACE_TYPE = PortNamespace
