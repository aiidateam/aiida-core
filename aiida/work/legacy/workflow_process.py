# -*- coding: utf-8 -*-

from aiida.orm import load_workflow
import plum.process
import plum.util
from aiida.common.lang import override
from aiida.work.process import Process


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."


class WorkflowProcess(Process):
    _WF_PK = 'wf_pk'
    _WF_CLASS = None # This will be filled in by build

    @classmethod
    def build(cls, wf_class):
        """
        Build the workflow process from an existing Workflow class.

        :param wf_class: The existing workflow class to use
        :return: A new class of type Process that can be used to run the
            workflow
        """

        def define(cls_, spec):
            super(WorkflowProcess, cls_).define(spec)

            spec.dynamic_input()
            spec.dynamic_output()

        class_name = "{}_{}".format(
            WorkflowProcess.__name__, plum.util.fullname(wf_class)
        )
        return type(class_name, (WorkflowProcess,),
                    {
                        Process.define.__name__: classmethod(define),
                        '_WF_CLASS': wf_class
                    })

    @override
    def on_create(self, pid, inputs, saved_instance_state):
        super(WorkflowProcess, self).on_create(pid, inputs, saved_instance_state)
        if saved_instance_state is None:
            self._wf = self._create_wf()
        else:
            self._wf = load_workflow(pk=saved_instance_state[self._WF_PK])

    @override
    def _run(self, **kwargs):
        from aiida.work.legacy.wait_on import wait_on_workflow
        self._wf.start()
        return wait_on_workflow(self._workflow_finished, self._wf.pk)

    def _create_wf(self):
        wf = self._WF_CLASS(params=self.inputs)
        return wf

    def _workflow_finished(self, wait_on):
        """
        The callback function that is called when the remote workflow
        is finished.

        :param wait_on: The original wait on that has finished
        :type wait_on: :class:`aiidaworklegacy.wait_on.WaitOnWorkflow`
        """
        for label, node in self._wf.get_results.iteritems():
            self.out(label, node)