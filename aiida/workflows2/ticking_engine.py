# -*- coding: utf-8 -*-

import plum.execution_engine
from plum.serial_engine import SerialEngine
import plum.parallel
import uuid

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class _Future(plum.execution_engine.Future):
    def __init__(self, engine):
        self._engine = engine

    def _process_finished(self):
        pass

class TickingEngine(plum.execution_engine.ExecutionEngine):
    class ProcessInfo(object):
        @classmethod
        def from_process(cls, pid, process, inputs, future):
            return cls(pid, process=process, inputs=inputs)

        @classmethod
        def from_record(cls, record):
            return cls(record.pid, record=record)

        def __init__(self, pid, process=None, inputs=None, future=None, wait_on=None, record=None):
            self._process = process
            self.inputs = inputs
            self.pid = pid
            self.waiting_on = wait_on
            self.futures = []
            if future:
                self.futures.append(future)
            self.record = record

        @property
        def process(self):
            if self._process is None:
                self._load_process()
            return self._process

        def _load_process(self):
            assert not self.process
            assert (self.record and self.record.has_checkpoint())

            self._process = self.record.create_process_from_checkpoint()
            self.inputs = self.record.inputs

    def __init__(self, persistence=None):
        self._current_processes = {}
        self._persistence = persistence
        self._serial_engine = SerialEngine()

    def submit(self, process, inputs):
        fut = _Future(self)
        pid = self._create_pid()
        self._current_processes[pid] = self.ProcessInfo.from_process(pid, process, inputs, fut)
        return fut

    def run(self, process, inputs):
        return self._serial_engine.run(process, inputs)

    def get_process(self, pid):
        proc_info = self._current_processes.get(pid, None)
        if proc_info:
            return proc_info.process
        else:
            return self._serial_engine.get_process(pid)

    def _create_pid(self):
        return uuid.uuid1()
