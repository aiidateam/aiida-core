import plum
from . import process
from . import rmq
from . import transport
from . import utils
from .default_loop import ResultAndPid

__all__ = ['Runner', 'create_daemon_runner', 'create_runner']


def _get_process_instance(process_class, *args, **kwargs):
    """
    Get a Process instance for a workchain or workfunction

    :param process_class: The workchain or workfunction to instantiate
    :param args: The positional arguments (only for workfunctions)
    :param kwargs: The keyword argument pairs
    :return: The process instance
    :rtype: :class:`aiida.process.Process`
    """

    if isinstance(process_class, process.Process):
        # Nothing to do
        return process_class
    elif utils.is_workfunction(process_class):
        wf_class = process.FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return wf_class(inputs=inputs)
    elif issubclass(process_class, process.Process):
        # No need to consider args as a Process can't deal with positional
        # arguments anyway
        return process_class(inputs=kwargs)
    else:
        raise TypeError("Unknown type for process_class '{}'".format(process_class))


def _object_factory(loop, process_class, *args, **kwargs):
    from aiida.work.process import FunctionProcess

    if utils.is_workfunction(process_class):
        wf_class = FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return wf_class(inputs=inputs)
    else:
        # Try instantiating as normal
        return process_class(*args, **kwargs)


class Runner(plum.PersistableEventLoop):
    def __init__(self, enable_transport=False, submit_to_daemon=True,
                 rmq_control_panel=None):
        super(Runner, self).__init__()

        if submit_to_daemon and not rmq_control_panel:
            raise ValueError("If you want to submit to daemon you must provide an RMQ control panel")

        self.set_object_factory(_object_factory)
        self._transport = None
        self._submit_to_daemon = submit_to_daemon

        # These should be last because they actually do a direct insert of objects
        self._rmq_control_panel = rmq_control_panel
        if rmq_control_panel is not None:
            self._insert(rmq_control_panel)

        if enable_transport:
            self._transport = transport.TransportQueue()
            self._insert(self._transport)

    @property
    def transport(self):
        return self._transport

    @property
    def rmq(self):
        return self._rmq_control_panel

    def run(self, process_class_or_workfunction, *args, **inputs):
        """
        This method blocks and runs the given process with the supplied inputs.
        It returns the outputs as produced by the process. 
        
        :param proc_class: The process class to run 
        :param inputs: The process inputs 
        :return: The process outputs
        """
        with self._create_child_runner() as child:
            proc = _get_process_instance(process_class_or_workfunction, *args, **inputs)
            child.insert(proc)
            return child.run_until_complete(proc)

    def run_get_pid(self, process_class_or_workfunction, *args, **inputs):
        with self._create_child_runner() as child:
            proc = _get_process_instance(process_class_or_workfunction, *args, **inputs)
            child.insert(proc)
            return ResultAndPid(~proc, proc.pid)

    def submit(self, process_class, *args, **inputs):
        if self._submit_to_daemon:
            return self.rmq.launch(process_class, inputs)
        else:
            return self.create(process_class, *args, inputs=inputs)

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
    rmq_panel = None
    if rmq_control_panel is not None:
        rmq_panel = rmq.create_control_panel(**rmq_control_panel)

    return Runner(
        enable_transport=enable_transport,
        submit_to_daemon=submit_to_daemon,
        rmq_control_panel=rmq_panel
    )


def create_daemon_runner(rmq_prefix='aiida', rmq_create_connection=None):
    if rmq_create_connection is None:
        rmq_create_connection = rmq._create_connection

    runner = Runner(
        enable_transport=True,
        submit_to_daemon=False,
        rmq_control_panel=rmq.create_control_panel(
            prefix=rmq_prefix, create_connection=rmq_create_connection
        )
    )

    rmq.insert_all_subscribers(runner, rmq_prefix, get_connection=rmq_create_connection)

    return runner
