import plum
from . import process
from . import transport
from . import utils
from .default_loop import ResultAndPid


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


class Runner(plum.PersistableEventLoop):
    def __init__(self, enable_transport=False, submit_to_daemon=True):
        super(Runner, self).__init__()

        self._transport = None
        self._submit_to_daemon = submit_to_daemon

        if enable_transport:
            self._transport = self.create(transport.TransportQueue)

    @property
    def transport(self):
        return self._transport

    def run(self, process_class_or_workfunction, *args, **inputs):
        """
        This method blocks and runs the given process with the supplied inputs.
        It returns the outputs as produced by the process. 
        
        :param proc_class: The process class to run 
        :param inputs: The process inputs 
        :return: The process outputs
        """
        child = self._create_child_runner()
        proc = _get_process_instance(process_class_or_workfunction, *args, **inputs)
        child.insert(proc)
        return child.run_until_complete(proc)

    def run_get_pid(self, process_class_or_workfunction, *args, **inputs):
        child = self._create_child_runner()
        proc = _get_process_instance(process_class_or_workfunction, *args, **inputs)
        child.insert(proc)

        return ResultAndPid(child.run_until_complete(proc), proc.pid)

    def submit(self, process_class, **inputs):
        if self._submit_to_daemon:
            raise NotImplementedError("STOP, it's not ready yet!")
        else:
            proc = _get_process_instance(process_class, **inputs)
            self.insert(proc)
            return proc

    def _create_child_runner(self):
        if self._transport:
            enable_transport = True
        else:
            enable_transport = False

        return Runner(enable_transport, self._submit_to_daemon)
