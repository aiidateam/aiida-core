import plum
from . import class_loader
from . import process
from . import rmq
from . import transport
from . import utils
from .default_loop import ResultAndPid
from apricotpy.persistable.core import Bundle

__all__ = ['Runner', 'create_daemon_runner', 'create_runner']


def _object_factory(loop, process_class, *args, **kwargs):
    from aiida.work.process import FunctionProcess

    if utils.is_workfunction(process_class):
        wf_class = FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return wf_class(loop=loop, inputs=inputs)
    else:
        return process_class(loop=loop, *args, **kwargs)


class Runner(plum.PersistableEventLoop):
    def __init__(self, enable_transport=False, submit_to_daemon=True):
        super(Runner, self).__init__()

        if submit_to_daemon and not rmq_control_panel:
            raise ValueError("If you want to submit to daemon you must provide an RMQ control panel")

        self.set_object_factory(_object_factory)
        self._transport = None
        self._submit_to_daemon = submit_to_daemon

        if enable_transport:
            self._transport = transport.TransportQueue(self)

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
            proc = child.create(process_class, *args, **inputs)
            return child.run_until_complete(proc)

    def run_get_pid(self, process_class, *args, **inputs):
        with self._create_child_runner() as child:
            proc = self.create(process_class, *args, **inputs)
            return ResultAndPid(~proc, proc.pid)

    def submit(self, process_class, *args, **inputs):
        if self._submit_to_daemon:
            process = _self.create(process_class, *args, **inputs)
            bundle = Bundle(process, class_loader=class_loader._CLASS_LOADER)
            return self.rmq.launch(bundle)
        else:
            return self.create(process_class, *args, **inputs)

    def _create_child_runner(self):
        if self._transport:
            enable_transport = True
        else:
            enable_transport = False

        return Runner(
            enable_transport,
            self._submit_to_daemon,
            rmq_control_panel=self._rmq_control_panel
        )


def create_runner(enable_transport=True, submit_to_daemon=True, rmq_control_panel={}):
    runner = Runner(
        enable_transport=enable_transport,
        submit_to_daemon=submit_to_daemon
    )

    if rmq_control_panel is not None:
        rmq_panel = rmq.create_control_panel(loop=runner, **rmq_control_panel)
        runner.set_rmq_control_panel(rmq_panel)

    return runner


def create_daemon_runner(rmq_prefix='aiida', rmq_create_connection=None):
    runner = Runner(
        enable_transport=True,
        submit_to_daemon=False,
    )

    if rmq_create_connection is None:
        rmq_create_connection = rmq._create_connection

    rmq_panel = rmq_control_panel=rmq.create_control_panel(
        prefix=rmq_prefix, create_connection=rmq_create_connection, loop=runner
    )
    runner.set_rmq_control_panel(rmq_panel)

    rmq.insert_all_subscribers(runner, rmq_prefix, get_connection=rmq_create_connection)

    return runner
