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
    PK = "pk"

    def __init__(self, pk, loop):
        super(WaitOnWorkflow, self).__init__(loop)
        self._pk = pk
        self._init()

    @override
    def save_instance_state(self, out_state):
        super(WaitOnWorkflow, self).save_instance_state(out_state)
        out_state[self.PK] = self._pk
        out_state.set_class_loader(class_loader)

    @override
    def load_instance_state(self, saved_state, loop):
        super(WaitOnWorkflow, self).load_instance_state(saved_state, loop)
        self._pk = saved_state[self.PK]
        self._init()

    def _init(self):
        self.loop().messages().add_listener(
            self._workflow_finished, "legacy_workflow.{}".format(self._pk))

        wf = load_workflow(pk=self._pk)
        if wf.get_state() in [wf_states.FINISHED, wf_states.ERROR]:
            self._done()

    def _workflow_finished(self, subject, body):
        self._done()

    def _done(self):
        self.future().set_result(True)
        self.loop().messages().remove_listener(self)
