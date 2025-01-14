###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing components from the workflow engine"""

import plumpy

from aiida.engine import Process
from aiida.orm import Bool, CalcJobNode, Data, WorkflowNode


class DummyProcess(Process):
    """A Process that does nothing when it runs."""

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.inputs.valid_type = Data
        spec.outputs.valid_type = Data

    async def run(self):
        pass


class AddProcess(Process):
    """A simple Process that adds two integers."""

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('a', required=True)
        spec.input('b', required=True)
        spec.output('result', required=True)

    async def run(self):
        summed = self.inputs.a + self.inputs.b
        self.out(summed.store())


class BadOutput(Process):
    """A Process that emits an output that isn't an AiiDA Data type."""

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.outputs.valid_type = Data

    async def run(self):
        self.out('bad_output', 5)


class ExceptionProcess(Process):
    """A Process that raises a RuntimeError when run."""

    _node_class = WorkflowNode

    async def run(self):
        raise RuntimeError('CRASH')


class WaitProcess(Process):
    """A Process that waits until it is asked to continue."""

    _node_class = WorkflowNode

    async def run(self):
        return plumpy.Wait(self.next_step)

    def next_step(self):
        pass


class InvalidateCaching(Process):
    """A process which invalidates cache for some exit codes."""

    _node_class = CalcJobNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('return_exit_code', valid_type=Bool)
        spec.exit_code(
            123, 'GENERIC_EXIT_CODE', message='This process should not be used as cache.', invalidates_cache=True
        )

    async def run(self):
        if self.inputs.return_exit_code:
            return self.exit_codes.GENERIC_EXIT_CODE


class IsValidCacheHook(Process):
    """A process which overrides the hook for checking if it is valid cache."""

    _node_class = CalcJobNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('not_valid_cache', valid_type=Bool, default=lambda: Bool(False))

    async def run(self):
        pass

    @classmethod
    def is_valid_cache(cls, node):
        return super().is_valid_cache(node) and not node.inputs.not_valid_cache.value
