
from aiida.workflows2.persistance.active_process import ActiveProcessRecord,\
    ActiveProcessStatus
import json
import tempfile
import os
import glob
import getpass
import csv
from enum import IntEnum

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

_STORE_DIRECTORY = os.path.join(tempfile.gettempdir(), "aiida_processes")


class _ProcessAttributes(IntEnum):
    TYPE = 0
    ID = 1
    PARENT_ID = 2
    CLASS_ID = 3
    STATUS = 4
    USER = 5
    INPUTS = 6


class FileActiveProcess(ActiveProcessRecord):
    _PROCESS_LABEL = "p"
    _WORKFLOW_LABEL = "w"
    _num_processes = 0

    @classmethod
    def generate_id(cls):
        pid = cls._num_processes
        cls._num_processes += 1
        return pid

    @classmethod
    def load_all(cls):
        process_records = []
        for filename in glob.glob(os.path.join(_STORE_DIRECTORY, "*.proc")):
            with open(filename) as csvfile:
                attributes = next(csv.reader(csvfile))
                proc = cls.build(attributes)
                if proc:
                    process_records.append(proc)
        return process_records

    @classmethod
    def build(cls, attributes):
        if attributes[_ProcessAttributes.TYPE] == cls._PROCESS_LABEL:
            return FileActiveProcess(
                attributes[_ProcessAttributes.CLASS_ID],
                json.loads(attributes[_ProcessAttributes.INPUTS]),
                id=attributes[_ProcessAttributes.ID],
                parent_id=attributes[_ProcessAttributes.PARENT_ID],
                _user=attributes[_ProcessAttributes.USER],
            )

    def __init__(self, process_class, inputs, id=None, parent_id=None,
                 _user=None):
        if id:
            self._id = id
        else:
            self._id = self.generate_id()

        self._parent_id = parent_id
        self._process_class = process_class
        self._status = ActiveProcessStatus.RUNNING
        self._inputs = inputs
        if _user:
            self._user = _user
        else:
            self._user = getpass.getuser()

        self._filename = "{}.proc".format(self.id)

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
        if not os.path.exists(_STORE_DIRECTORY):
            os.makedirs(_STORE_DIRECTORY)

        with open(os.path.join(_STORE_DIRECTORY, self._filename), 'w') as f:
            # Gather all the things we want to store in order
            info = [self._PROCESS_LABEL, self.id, self.parent_id,
                    self.process_class, self.status, self.user,
                    json.dumps(self.inputs)]
            csv.writer(f).writerow(info)

    def delete(self):
        try:
            os.remove(os.path.join(_STORE_DIRECTORY, self._filename))
        except OSError:
            pass

