import plum
import inspect
from collections import namedtuple
from contextlib import contextmanager

import aiida.orm
from . import rmq
from . import transport
from . import utils

__all__ = ['Runner', 'create_daemon_runner', 'create_runner', 'new_runner']

ResultAndCalcNode = namedtuple("ResultWithPid", ["result", "calc"])
ResultAndPid = namedtuple("ResultWithPid", ["result", "pid"])

_runner = None


def get_runner():
    global _runner
    if _runner is None:
        _runner = new_runner()
    return _runner


def set_runner(runner):
    global _runner
    _runnner = runner


def new_runner(**kwargs):
    return Runner({}, **kwargs)


def convert_to_inputs(workfunction, *args, **kwargs):
    """
    """
    arg_labels, varargs, keywords, defaults = inspect.getargspec(workfunction)

    inputs = {}
    inputs.update(kwargs)
    inputs.update(dict(zip(arg_labels, args)))

    return inputs


def _object_factory(process_class, *args, **kwargs):
    return process_class(*args, **kwargs)


def _ensure_process(process, runner, input_args, input_kwargs, *args, **kwargs):
    """ Take a process class, a process instance or a workfunction along with
    arguments and return a process instance"""
    from aiida.work.processes import Process
    if isinstance(process, Process):
        assert len(input_args) == 0
        assert len(input_kwargs) == 0
        return process

    return _create_process(process, runner, input_args, input_kwargs, *args, **kwargs)


def _create_process(process, runner, input_args=(), input_kwargs={}, *args, **kwargs):
    """ Create a process instance from a process class or workfunction """
    inputs = _create_inputs_dictionary(process, *input_args, **input_kwargs)
    return _object_factory(process, runner=runner, inputs=inputs, *args, **kwargs)


def _create_inputs_dictionary(process, *args, **kwargs):
    """ Create an inputs dictionary for a process or workfunction """
    if utils.is_workfunction(process):
        inputs = convert_to_inputs(process, *args, **kwargs)
    else:
        inputs = kwargs
        assert len(args) == 0, "Processes do not take positional arguments"

    return inputs


class Runner(object):
    _poll_interval = 5.

    def __init__(self, rmq_config, loop=None, poll_interval=5.):
        self._loop = loop if loop is not None else plum.new_event_loop()
        self._poll_interval = poll_interval

        self._transport = transport.TransportQueue(self._loop)
        self._rmq_config = rmq_config
        self._rmq = None  # construct from config

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def loop(self):
        return self._loop

    @property
    def rmq(self):
        return self._rmq

    @property
    def transport(self):
        return self._transport

    def close(self):
        pass

    def run(self, process, *args, **inputs):
        """
        This method blocks and runs the given process with the supplied inputs.
        It returns the outputs as produced by the process. 
        
        :param process: The process class or workfunction to run
        :param inputs: Workfunction positional arguments
        :return: The process outputs
        """
        if utils.is_workfunction(process):
            return process(*args, **inputs)
        else:
            with self.child_runner() as runner:
                process = _ensure_process(process, runner, input_args=args, input_kwargs=inputs)
                return process.execute()

    def run_get_node(self, process, *args, **inputs):
        if utils.is_workfunction(process):
            return process.run_get_node(*args, **inputs)
        with self.child_runner() as runner:
            process = _ensure_process(process, runner, input_args=args, input_kwargs=inputs)
            return ResultAndCalcNode(process.execute(), process.calc)

    def run_get_pid(self, process, *args, **inputs):
        result, node = self.run_get_node(process, *args, **inputs)
        return ResultAndPid(result, node.pid)

    def submit(self, process_class, *args, **inputs):
        assert not utils.is_workfunction(process_class), "Cannot submit a workfunction"
        process = _create_process(process_class, self, input_args=args, input_kwargs=inputs)
        process.play()
        return process.calc

    def call_on_legacy_workflow_finish(self, pk, callback):
        legacy_wf = aiida.orm.load_workflow(pk=pk)
        self._poll_legacy_wf(legacy_wf, callback)

    def call_on_calculation_finish(self, pk, callback):
        calc_node = aiida.orm.load_node(pk=pk)
        self._poll_calculation(calc_node, callback)

    def _submit(self, process, *args, **kwargs):
        pass

    @contextmanager
    def child_runner(self):
        runner = Runner(self._rmq_config)
        try:
            yield runner
        finally:
            runner.close()

    def _poll_legacy_wf(self, workflow, callback):
        if workflow.has_finished_ok() or workflow.has_failed():
            self._loop.add_callback(callback, workflow.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_legacy_wf, workflow, callback)

    def _poll_calculation(self, calc_node, callback):
        if calc_node.has_finished():
            self._loop.add_callback(callback, calc_node.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_calculation, calc_node, callback)


def create_runner(submit_to_daemon=True, rmq_control_panel={}):
    runner = Runner(submit_to_daemon=submit_to_daemon)

    if rmq_control_panel is not None:
        rmq_panel = rmq.create_control_panel(loop=plum.get_event_loop(), **rmq_control_panel)
        runner.set_rmq_control_panel(rmq_panel)

    return runner


def create_daemon_runner(rmq_prefix='aiida', rmq_create_connection=None):
    runner = Runner(submit_to_daemon=False)

    if rmq_create_connection is None:
        rmq_create_connection = rmq._create_connection

    rmq_panel = rmq.create_control_panel(
        prefix=rmq_prefix, create_connection=rmq_create_connection, loop=plum.get_event_loop()
    )
    runner.set_rmq_control_panel(rmq_panel)

    rmq.insert_all_subscribers(runner, rmq_prefix, get_connection=rmq_create_connection)

    return runner
