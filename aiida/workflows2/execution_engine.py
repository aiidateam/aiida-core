# -*- coding: utf-8 -*-

import plum.execution_engine
from aiida.workflows2.persistance.active_factory import create_process_record
from plum.process import ProcessListener

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class TrackingExecutionEngine(plum.execution_engine.ExecutionEngine, ProcessListener):
    _NUM_PROCESSES = 0

    class Delegate(plum.execution_engine.ExecutionEngine, ProcessListener):
        def __init__(self, exec_engine, parent_process):
            self._exec_engine = exec_engine
            self._parent_process = parent_process

        def run(self, process):
            process.add_process_listener(self)
            process.run(TrackingExecutionEngine.Delegate(self._exec_engine, process))

        def on_process_starting(self, process, inputs):
            self._exec_engine._add_process(process, inputs, self._parent_process)

        def on_process_finishing(self, process):
            process.remove_process_listener(self)
            self._exec_engine._remove_process(process)

    def __init__(self):
        self._records = {}
        self._processes = {}

    # def load(self, records):
    #     for record in records:
    #         proc_class = self.load(record.process_class)
    #         proc = proc_class.create()

    def run(self, process):
        """
        Run a process.
        :param process: The process to run
        """
        process.add_process_listener(self)
        process.run(TrackingExecutionEngine.Delegate(self, process))

    def push(self, process):
        return TrackingExecutionEngine.Delegate(self, process)

    def get_pid(self, process):
        for pid, proc in self._processes.iteritems():
            if proc is process:
                return pid
        return None

    def on_process_starting(self, process, inputs):
        self._add_process(process, inputs, None)

    def on_process_finishing(self, process):
        process.remove_process_listener(self)
        self._remove_process(process)

    def _add_process(self, process, inputs, parent):
        pid = self._generate_id()
        parent_pid = None
        if parent:
            parent_pid = self.get_pid(parent)

        record = create_process_record(process, inputs, pid, parent_pid)
        record.save()
        self._records[pid] = record
        self._processes[pid] = process

    def _remove_process(self, process):
        pid = self.get_pid(process)
        record = self._records.pop(pid)
        record.delete()
        self._processes.pop(pid)

    def _get_record(self, process):
        return self._records.get(self.get_pid(process), None)

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

    @classmethod
    def _generate_id(cls):
        pid = cls._NUM_PROCESSES
        cls._NUM_PROCESSES += 1
        return pid
