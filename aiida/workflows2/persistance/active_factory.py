# -*- coding: utf-8 -*-

from aiida.workflows2.persistance.active_process import ActiveProcessRecord,\
    ActiveProcessStatus
import aiida.workflows2.persistance.file_store as file_store

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class InMemoryActiveProcess(ActiveProcessRecord):
    _num_processes = 0

    def __init__(self, process, parent_id=None):
        import getpass

        self._id = self.generate_id()
        self._parent_id = parent_id
        self._process_class = process.__class__
        self._status = ActiveProcessStatus.RUNNING
        self._inputs = process.bound_inputs
        self._user = getpass.getuser()

    @property
    def id(self):
        return self._id

    @property
    def parent_id(self):
        return self._parent_id

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


def create_process_record(process, inputs, id, parent_id=None):
    return file_store.FileActiveProcess(
        process.__class__.__name__,
        {label: inp.uuid for label, inp in inputs.iteritems()},
        id, parent_id)

#
# def create_workflow_record(process, inputs):
#     return file_store.FileActiveWorkflow(
#         process.__class__,
#         {label: inp.uuid for label, inp in inputs.iteritems()})


def load_all_process_records():
    return file_store.FileActiveProcess.load_all()
