import plum
import inspect
from contextlib import contextmanager
from . import rmq
from . import transport
from . import utils


__all__ = ['Runner', 'create_daemon_runner', 'create_runner']


_runner = None

def get_runner():
    global _runner
    if _runner is None:
        _runner = Runner({})
    return _runner


def set_runner(runner):
    global _runner
    _runnner = runner



def convert_to_inputs(workfunction, *args, **kwargs):
    """
    """
    arg_labels, varargs, keywords, defaults = inspect.getargspec(workfunction)

    inputs = {}
    inputs.update(kwargs)
    inputs.update(dict(zip(arg_labels, args)))

    return inputs


def _object_factory(process_class, *args, **kwargs):
    from aiida.work.process import FunctionProcess

    if utils.is_workfunction(process_class):
        wf_class = FunctionProcess.build(process_class._original, **kwargs['inputs'])
        return wf_class(**kwargs)
    else:
        return process_class(*args, **kwargs)


class Runner(object):
    def __init__(self, rmq_config, loop=None):

        if loop is None:
            self._loop = loop
        else:
            self._loop = plum.new_event_loop()

        self._transport = transport.TransportQueue(self._loop)
        self._rmq_config = rmq_config
        self._rmq = None # construct from config

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

    def run(self, process_class, *args, **inputs):
        """
        This method blocks and runs the given process with the supplied inputs.
        It returns the outputs as produced by the process. 
        
        :param process_class: The process class to run 
        :param inputs: The process inputs 
        :return: The process outputs
        """
        with self.child_runner() as runner:
            process = self._ensure_process(process_class, runner, input_args=args, input_kwargs=inputs)
            return process.execute()

    def run_get_pid(self, process_class, *args, **inputs):
        with self.child_runner() as runner:
            process = self._ensure_process(process_class, runner, input_args=args, input_kwargs=inputs)
            return ResultAndPid(process.execute(), process.pid)

    def submit(self, process_class, *args, **inputs):
        process = self._ensure_process(process_class, self, input_args=args, input_kwargs=inputs)
        process.play()
        return process.calc

    @contextmanager
    def child_runner(self):
        try:
            yield Runner(self._rmq_config)
        finally:
            pass

    def _ensure_process(self, process, runner, input_args, input_kwargs):
        from aiida.work.process import Process
        if isinstance(process, Process):
            assert len(input_args) == 0
            assert len(input_kwargs) == 0
            return process

        if utils.is_workfunction(process):
            inputs = convert_to_inputs(process, *input_args, **input_kwargs)
        else:
            inputs = input_kwargs
            assert len(input_args) == 0

        return _object_factory(process, runner=runner, inputs=inputs)



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
