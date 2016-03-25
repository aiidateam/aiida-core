# -*- coding: utf-8 -*-

from aiida.workflows2.active_records import ActiveProcessRecord,\
    ActiveWorkflowRecord, ActiveProcessStatus

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class InMemoryActiveProcess(ActiveProcessRecord):
    def __init__(self, process):
        import getpass

        self._id = 0
        self._process_class = process.__class__
        self._status = ActiveProcessStatus.RUNNING
        self._inputs = process.bound_inputs
        self._user = getpass.getuser()

    @property
    def id(self):
        return self._id

    @property
    def process_class(self):
        return self._process_class

    @property
    def status(self):
        return self._status

    @property
    def user(self):
        return self._user

    @property
    def inputs(self):
        return self._inputs

    def save(self):
        pass

    def delete(self):
        pass


class InMemoryActiveWorkflow(InMemoryActiveProcess, ActiveWorkflowRecord):
    pass


def create_process_record(process):
    return InMemoryActiveProcess(process)


def create_workflow_record(process):
    return InMemoryActiveWorkflow(process)
