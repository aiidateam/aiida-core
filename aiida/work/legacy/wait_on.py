# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from plum.wait import WaitOn
from aiida.orm.utils import load_workflow
from aiida.common.datastructures import wf_states
from aiida.common.lang import override
from aiida.work.globals import class_loader, REGISTRY


class WaitOnProcessTerminated(WaitOn):
    PK = "pk"

    @override
    def __init__(self, pk, loop):
        super(WaitOnProcessTerminated, self).__init__(loop)
        self._pk = pk
        self._init()

    @override
    def load_instance_state(self, saved_state, loop):
        super(WaitOnProcessTerminated, self).load_instance_state(saved_state, loop)
        self._pk = saved_state[self.PK]
        self._init()

    @override
    def save_instance_state(self, out_state):
        super(WaitOnProcessTerminated, self).save_instance_state(out_state)
        out_state[self.PK] = self._pk
        out_state.set_class_loader(class_loader)

    def _calc_terminated(self, subject, body):
        self._done()

    def _init(self):
        # Need to start listening first so we don't do the following:
        # 1. REGISTRY.has_finished(..) returns False
        # <- Calculation terminates
        # 2. Start listening
        # 3. Wait forever because the calculation has finished already

        # Start listening to all the states we care about
        messages = self.loop().messages()
        for proc_type in ['calc', 'process']:
            for state in ['stopped', 'failed']:
                evt = "{}.{}.{}".format(proc_type, self._pk, state)
                messages.add_listener(self._calc_terminated, evt)

        if REGISTRY.has_finished(self._pk):
            self._done()

    def _done(self):
        self.future().set_result(True)
        self.loop().messages().remove_listener(self)


class WaitOnWorkflow(WaitOn):
    PK = 'PK'
    RETURN_RESULTS = 'RETURN_RESULTS'
    POLL_INTERVAL = 'POLL_INTERVAL'
    DEFAULT_POLL_INTERVAL = 30  # seconds

    def __init__(self, pk, return_results=False,
                 poll_interval=DEFAULT_POLL_INTERVAL):
        super(WaitOnWorkflow, self).__init__()
        self._workflow = load_workflow(pk=pk)
        self._return_outputs = return_results
        self._poll_interval = poll_interval

    def on_loop_inserted(self, loop):
        super(WaitOnWorkflow, self).on_loop_inserted(loop)
        self._check_if_finished()

    @override
    def save_instance_state(self, out_state):
        super(WaitOnWorkflow, self).save_instance_state(out_state)
        out_state[self.PK] = self._workflow.pk
        out_state[self.RETURN_RESULTS] = self._return_outputs
        out_state[self.POLL_INTERVAL] = self._poll_interval

    @override
    def load_instance_state(self, loop, saved_state):
        super(WaitOnWorkflow, self).load_instance_state(saved_state, loop)
        self._workflow = load_workflow(pk=saved_state[self.PK])
        self._return_outputs = saved_state[self.RETURN_RESULTS]
        self._poll_interval = saved_state[self.POLL_INTERVAL]

    def _check_if_finished(self):
        if self._workflow.get_state() in [wf_states.FINISHED, wf_states.ERROR]:
            self._done()
        else:
            self.loop().call_later(self._poll_interval, self._check_if_finished)

    def _done(self):
        if self._return_outputs:
            self.set_result(self._workflow.get_results())
        else:
            self.set_result(True)
