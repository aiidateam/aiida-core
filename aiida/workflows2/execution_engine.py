# -*- coding: utf-8 -*-

import plum.execution_engine
from aiida.workflows2.persistance.active_factory import create_process_record
from plum.process import ProcessListener

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class TrackingExecutionEngine(plum.execution_engine.ExecutionEngine, ProcessListener):
    """
    This execution engine keeps track of who called who so it's possible to
    recreate the call stack if needed for recalling a process or workflow.
    """
    _NUM_PROCESSES = 0

    class Delegate(plum.execution_engine.ExecutionEngine):
        def __init__(self, exec_engine, parent_process):
            self._exec_engine = exec_engine
            self._parent_process = parent_process

        def run(self, process, inputs):
            self._exec_engine._submit(process, inputs, self._parent_process)

    def __init__(self):
        self._records = {}
        self._processes = {}

    # def load(self, records):
    #     for record in records:
    #         proc_class = self.load(record.process_class)
    #         proc = proc_class.create()

    def run(self, process, inputs):
        """
        Run a process.
        :param process: The process to run
        """
        process._submit(process, inputs, None)

    def push(self, process):
        return TrackingExecutionEngine.Delegate(self, process)

    def get_pid(self, process):
        for pid, proc in self._processes.iteritems():
            if proc is process:
                return pid
        return None

    def _submit(self, process, inputs, parent):
        record = self._add_process(process, inputs, parent)
        process.run(inputs, TrackingExecutionEngine.Delegate(self, process),
                    record.instance_state)

    # Process messages ################################
    def on_process_starting(self, process, inputs):
        # TODO: Change status to starting
        pass

    def on_process_finialising(self, process):
        self._remove_process(process)
    ###################################################

    def _add_process(self, process, inputs, parent):
        process.add_process_listener(self)

        record = create_process_record(process, inputs)
        record.save()
        if parent:
            parent_pid = self.get_pid(parent)
            parent_record = self._records[parent_pid]
            parent_record.add_child(record.id)
            parent_record.save()

        self._records[record.id] = record
        self._processes[record.id] = process

        return record

    def _remove_process(self, process):
        process.remove_process_listener(self)
        pid = self.get_pid(process)

        # Check if anyone has this process as a child
        parent_pid = self._get_parent_pid(pid)
        if parent_pid:
            parent_record = self._records[parent_pid]
            parent_record.remove_child(pid)
            parent_record.save()

        record = self._records.pop(pid)
        record.delete()
        self._processes.pop(pid)

    def _get_record(self, process):
        return self._records.get(self.get_pid(process), None)

    def _get_parent_pid(self, child_pid):
        for record in self._records.itervalues():
            if record.has_child(child_pid):
                return record.id
        return None

    @staticmethod
    def load_class(classstring):
        """
        Load a class from a string
        """
        class_data = classstring.split(".")
        module_path = ".".join(class_data[:-1])
        class_name = class_data[-1]

        module = importlib.import_module(module_path)
        # Finally, we retrieve the Class
        return getattr(module, class_name)

