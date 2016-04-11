
from aiida.workflows2.persistance.active_process import ActiveProcessRecord,\
    ActiveProcessStatus, InstanceState
import pickle
import datetime
import tempfile
import os
import glob
import getpass


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

_STORE_DIRECTORY = os.path.join(tempfile.gettempdir(), "aiida_processes")


class FileInstanceState(InstanceState, dict):
    def __init__(self, process):
        super(FileInstanceState, self).__init__()
        self._process = process

    def save(self):
        self._process.save()


class FileActiveProcess(ActiveProcessRecord):
    _num_processes = 0

    @classmethod
    def generate_id(cls):
        pid = cls._num_processes
        cls._num_processes += 1
        return pid

    @classmethod
    def load(cls, fileobj):
        assert(not fileobj.closed)
        return pickle.load(fileobj)

    @classmethod
    def load_all(cls):
        process_records = []
        for filename in glob.glob(os.path.join(_STORE_DIRECTORY, "*.proc")):
            with open(filename) as f:
                proc = cls.load(f)
                if proc:
                    process_records.append(proc)
        return process_records

    def __init__(self, process_class, inputs, _user=None):

        self._id = self.generate_id()
        self._retronode_pk = 0
        self._process_class = process_class
        self._status = ActiveProcessStatus.RUNNING
        self._inputs = inputs
        if _user:
            self._user = _user
        else:
            self._user = getpass.getuser()

        self._filename = "{}.proc".format(self.id)
        self._last_saved = None
        self._instance_state = FileInstanceState(self)
        self._children = []

    @property
    def id(self):
        return self._id

    @property
    def retronode_pk(self):
        return self._retronode_pk

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

    @property
    def last_saved(self):
        return self._last_saved

    @property
    def instance_state(self):
        return self._instance_state

    def add_child(self, pid):
        self._children.append(pid)

    def remove_child(self, pid):
        self._children.remove(pid)

    def has_child(self, pid):
        return pid in self._children

    def save(self):
        if not os.path.exists(_STORE_DIRECTORY):
            os.makedirs(_STORE_DIRECTORY)

        with open(os.path.join(_STORE_DIRECTORY, self._filename), 'w') as f:
            # Gather all the things we want to store in order
            self._last_saved = datetime.now()
            pickle.dump(self, f)

    def delete(self):
        try:
            os.remove(os.path.join(_STORE_DIRECTORY, self._filename))
        except OSError:
            pass

