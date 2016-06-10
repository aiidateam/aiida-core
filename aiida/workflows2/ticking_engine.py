# -*- coding: utf-8 -*-

import threading
import concurrent.futures
from plum.wait import WaitOn
import plum.execution_engine
import plum.parallel
from aiida.workflows2.util import override
from enum import Enum

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


class ProcessStatus(Enum):
    QUEUEING = 0,
    RUNNING = 1,
    WAITING = 2,
    FINISHED = 3,


class _Future(plum.execution_engine.Future):
    class Status(Enum):
        CURRENT = 0
        CANCELLED = 1
        FINISHED = 2

    def __init__(self, engine, pid):
        self._engine = engine
        self._pid = pid
        self._status = self.Status.CURRENT
        self._done_callbacks = []
        self._result = None
        self._condition = None

    @property
    def pid(self):
        return self._pid

    def process_finished(self, result):
        self._status = self.Status.FINISHED
        self._result = result

        try:
            self._condition.set()
        except AttributeError:
            pass

        for fn in self._done_callbacks:
            fn(self)

    def cancel(self):
        self._engine.cancel(self._pid)
        self._status = self.Status.CANCELLED

    def cancelled(self):
        return self._status is self.Status.CANCELLED

    def running(self):
        return self._status is self.Status.CURRENT

    def done(self):
        return self._status in [self.Status.CANCELLED, self.Status.FINISHED]

    def result(self, timeout=None):
        if self._status is self.Status.CURRENT:
            self._condition = threading.Event()
            if not self._condition.wait(timeout):
                raise concurrent.futures.TimeoutError()
            self._condition = None

        return self._result

    def exception(self, timeout=None):
        return None

    def add_done_callback(self, fn):
        self._done_callbacks.append(fn)


class TickingEngine(plum.execution_engine.ExecutionEngine):
    class ProcessInfo(object):
        @classmethod
        def from_process(cls, process, inputs, future, status):
            return cls(process=process, inputs=inputs, future=future,
                       status=status)

        def __init__(self, process=None, inputs=None, future=None,
                     wait_on=None, status=None):
            self._process = process
            self.inputs = inputs
            self.waiting_on = wait_on
            self.futures = []
            if future:
                self.futures.append(future)
            self.status = status

        @property
        def process(self):
            return self._process

    def __init__(self, process_factory=None):
        if process_factory is None:
            from aiida.workflows2.process_factory import ProcessFactory
            process_factory = ProcessFactory()
        self._process_factory = process_factory

        self._current_processes = {}
        self._process_queue = []

    @override
    def submit(self, process_class, inputs, checkpoint=None):
        if checkpoint is None:
            process =\
                self._process_factory.create_process(process_class, inputs)
        else:
            process, wait_on = self._process_factory.recreate_process(
                process_class, checkpoint)
        fut = _Future(self, process.pid)
        # Put it in the queue
        self._current_processes[process.pid] =\
            self.ProcessInfo.from_process(process, inputs, fut,
                                          ProcessStatus.QUEUEING)
        return fut

    def tick(self):
        for proc_info in self._current_processes.values():
            if proc_info.status is ProcessStatus.QUEUEING:
                self._start_process(proc_info)
            elif proc_info.status is ProcessStatus.WAITING:
                if proc_info.waiting_on.is_ready():
                    self._continue_process(proc_info)
            elif proc_info.status is ProcessStatus.FINISHED:
                for fut in proc_info.futures:
                    fut.process_finished(proc_info.process.get_last_outputs())
                del self._current_processes[proc_info.process.pid]
            else:
                raise RuntimeError(
                    "Process should not be in state {}".format(proc_info.status)
                )
        return len(self._current_processes) > 0

    def cancel(self, pid):
        proc_info = self._current_processes[pid]
        if proc_info.status is ProcessStatus.QUEUEING:
            del self._current_processes[pid]
        else:
            # TODO: Queue up for cancelling next time
            pass

    def _start_process(self, proc_info):
        """
        Send the appropriate messages and start the Process.
        :param proc_info: The process information
        :return: None if the Process is waiting on something, the return value otherwise,
        :note: Do not use a return value of None from this function to indicate that process
        is not waiting on something as the process may simply have returned None.  Instead
        use proc_info.waiting_on is None.
        """
        assert proc_info.status is ProcessStatus.QUEUEING

        process = proc_info.process
        inputs = proc_info.inputs

        ins = process._create_input_args(inputs)
        process.on_start(self)
        retval = process._run(**ins)
        if isinstance(retval, WaitOn):
            self._wait_process(proc_info, retval)
        else:
            self._finish_process(proc_info, retval)
            return retval

    def _continue_process(self, proc_info):
        assert proc_info.status is ProcessStatus.WAITING
        assert proc_info.waiting_on,\
            "Cannot continue a process that was not waiting"

        # Get the WaitOn callback function name and call it
        # making sure to reset the waiting_on
        wait_on = proc_info.waiting_on
        proc_info.waiting_on = None
        retval = getattr(proc_info.process, wait_on.callback)(wait_on)

        # Check what to do next
        if isinstance(retval, WaitOn):
            self._wait_process(proc_info, retval)
        else:
            self._finish_process(proc_info, retval)
            return retval

    def _wait_process(self, proc_info, wait_on):
        assert not proc_info.waiting_on,\
            "Cannot wait on a process that is already waiting"

        proc_info.waiting_on = wait_on
        proc_info.process.on_wait()

        proc_info.status = ProcessStatus.WAITING

    def _finish_process(self, proc_info, retval):
        assert not proc_info.waiting_on,\
            "Cannot finish a process that is waiting"

        proc_info.process.on_finish(retval)
        proc_info.status = ProcessStatus.FINISHED

