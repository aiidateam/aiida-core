

import plum.process_factory
from plum.wait import WaitOn
from plum.persistence.checkpoint import Checkpoint
from aiida.workflows2.util import override


__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class ProcessFactory(plum.process_factory.ProcessFactory):
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
        from aiida.workflows2.process import Process

        if checkpoint.wait_on_instance_state:
            wait_on = WaitOn.create_from(
                checkpoint.wait_on_instance_state, self)
        else:
            wait_on = None

        proc = checkpoint.process_class(self._store_provenance)
        proc.on_recreate(None, checkpoint.process_instance_state)

        return proc, wait_on

    @override
    def destroy_process(self, process):
        pass

    @override
    def create_checkpoint(self, process, wait_on):
        cp = Checkpoint()
        cp.pid = process.pid
        cp.process_class = process.__class__
        process.save_instance_state(cp.process_instance_state)
        if wait_on is not None:
            wait_on.save_instance_state(cp.wait_on_instance_state)

        return cp
