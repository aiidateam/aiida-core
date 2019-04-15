# -*- coding: utf-8 -*-


import plum.process_factory
from plum.wait import WaitOn
from plum.persistence.checkpoint import Checkpoint
from aiida.common.lang import override
from aiida.workflows2.legacy.job_process import JobProcess
from aiida.workflows2.process import FunctionProcess

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."


class ProcessFactory(plum.process_factory.ProcessFactory):
    CALC_CLASS = 'calc_class'
    FUNC = 'func'

    def __init__(self, store_provenance=True):
        # Keep track of the running processes
        self._store_provenance = store_provenance

    @override
    def create_process(self, process_class, inputs=None):
        from aiida.workflows2.process import Process
        assert(issubclass(process_class, Process))

        proc = process_class(self._store_provenance)
        proc.on_create(None, inputs)

        return proc

    @override
    def recreate_process(self, checkpoint):
        if checkpoint.wait_on_instance_state:
            wait_on = WaitOn.create_from(
                checkpoint.wait_on_instance_state, self)
        else:
            wait_on = None

        if self.CALC_CLASS in checkpoint.process_instance_state:
            # It's a wrapped legacy calculation class, so rebuild it.
            ProcClass = JobProcess.build(
                checkpoint.process_instance_state[self.CALC_CLASS])
            proc = ProcClass(self._store_provenance)
        elif self.FUNC in checkpoint.process_instance_state:
            # It's a wrapped up workfunction, so rebuild it.
            # Hmm...not sure if this is possible
            return None, wait_on
        else:
            proc = checkpoint.process_class(self._store_provenance)
        proc.on_recreate(None, checkpoint.process_instance_state)

        return proc, wait_on

    @override
    def create_checkpoint(self, process, wait_on):
        cp = Checkpoint()

        cp.pid = process.pid
        if issubclass(process.__class__, JobProcess):
            cp.process_class = JobProcess
            cp.process_instance_state[self.CALC_CLASS] = process._CALC_CLASS
        elif issubclass(process.__class__, FunctionProcess):
            cp.process_class = FunctionProcess
            cp.process_instance_state[self.FUNC] = process._func
        else:
            cp.process_class = process.__class__
        process.save_instance_state(cp.process_instance_state)
        if wait_on is not None:
            wait_on.save_instance_state(cp.wait_on_instance_state)

        return cp
