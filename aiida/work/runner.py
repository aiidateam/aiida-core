import plum
from . import class_loader
from . import process
from . import rmq
from . import transport
from . import utils
from .default_loop import ResultAndPid

__all__ = ['Runner', 'create_daemon_runner', 'create_runner']


def _object_factory(process_class, *args, **kwargs):
    from aiida.work.process import FunctionProcess

    if utils.is_workfunction(process_class):
        wf_class = FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return wf_class(inputs=inputs)
    else:
        return process_class(*args, **kwargs)


class Runner(object):
    def __init__(self, submit_to_daemon=True):
        super(Runner, self).__init__()

        self._transport = None
        self._submit_to_daemon = submit_to_daemon
        self._rmq_control_panel = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def set_rmq_control_panel(self, rmq_control_panel):
        self._rmq_control_panel = rmq_control_panel

    @property
    def transport(self):
        return self._transport

    @property
    def rmq(self):
        return self._rmq_control_panel

    def run(self, process_class, *args, **inputs):
        """
        This method blocks and runs the given process with the supplied inputs.
        It returns the outputs as produced by the process. 
        
        :param process_class: The process class to run 
        :param inputs: The process inputs 
        :return: The process outputs
        """
        with self._create_child_runner() as child:
            proc = _object_factory(process_class, *args, **inputs)
            return proc.execute()

    def run_get_pid(self, process_class, *args, **inputs):
        with self._create_child_runner() as child:
            proc = _object_factory(process_class, *args, **inputs)
            return ResultAndPid(proc.execute(), proc.pid)

    def submit(self, process_class, *args, **inputs):
        if self._submit_to_daemon:
            process = _object_factory(process_class, *args, **inputs)
            return self.rmq.launch(process.uuid)
        else:
            return _object_factory(process_class, *args, **inputs)

    def _create_child_runner(self):

        runner = Runner(self._submit_to_daemon)

        runner.set_rmq_control_panel(self._rmq_control_panel)

        return runner


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
