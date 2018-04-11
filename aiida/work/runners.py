from collections import namedtuple
from contextlib import contextmanager
import inspect
import logging
import plumpy
import plumpy.rmq

import aiida.orm
from . import class_loader
from . import futures
from . import persistence
from . import rmq
from . import transports
from . import utils

__all__ = ['Runner', 'DaemonRunner', 'new_daemon_runner', 'new_runner', 'set_runner', 'get_runner']

_LOGGER = logging.getLogger(__name__)

ResultAndNode = namedtuple('ResultAndNode', ['result', 'node'])
ResultAndPid = namedtuple('ResultAndPid', ['result', 'pid'])

_runner = None


def get_runner():
    global _runner
    if _runner is None:
        _runner = new_runner()
    return _runner


def set_runner(runner):
    global _runner
    _runner = runner


def new_runner(**kwargs):
    """ Create a default runner optionally passing keyword arguments """
    if 'rmq_config' not in kwargs:
        kwargs['rmq_config'] = rmq.get_rmq_config()
    return Runner(**kwargs)


def new_daemon_runner(rmq_prefix='aiida', rmq_create_connection=None):
    """ Create a daemon runner """
    runner = Runner({}, rmq_submit=False, enable_persistence=True)
    return runner


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
    """
    Take a process class, a process instance or a workfunction along with
    arguments and return a process instance
    """
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
    _persister = None
    _rmq_connector = None
    _communicator = None

    def __init__(self, rmq_config=None, loop=None, poll_interval=0.,
                 rmq_submit=False, enable_persistence=True, persister=None):
        self._loop = loop if loop is not None else plumpy.new_event_loop()
        self._poll_interval = poll_interval

        self._transport = transports.TransportQueue(self._loop)

        if enable_persistence:
            self._persister = persister if persister is not None else persistence.AiiDAPersister()

        self._rmq_submit = rmq_submit
        if rmq_config is not None:
            self._setup_rmq(**rmq_config)
        elif self._rmq_submit:
            _LOGGER.warning('Disabling rmq submission, no RMQ config provided')
            self._rmq_submit = False

        # Save kwargs for creating child runners
        self._kwargs = {
            'rmq_config': rmq_config,
            'poll_interval': poll_interval,
            'rmq_submit': rmq_submit,
            'enable_persistence': enable_persistence
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def loop(self):
        return self._loop

    @property
    def rmq(self):
        return self._rmq

    @property
    def transport(self):
        return self._transport

    @property
    def persister(self):
        return self._persister

    @property
    def communicator(self):
        return self._communicator

    def start(self):
        """ Start the internal event loop """
        self._loop.start()

    def stop(self):
        """ Stop the internal event loop """
        self._loop.stop()

    def run_until_complete(self, future):
        """ Run the loop until the future has finished and return the result """
        return self._loop.run_sync(lambda: future)

    def close(self):
        self.stop()
        if self._rmq_connector is not None:
            self._rmq_connector.disconnect()

    def submit(self, process_class, *args, **inputs):
        """
        Submit the process with the supplied inputs to this runner immediately returning control to
        the interpreter. The return value will be the calculation node of the submitted process

        :param process: the process class to submit
        :param inputs: the inputs to be passed to the process
        :return: the calculation node of the process
        """
        assert not utils.is_workfunction(process_class), 'Cannot submit a workfunction'

        process_class, inputs = _expand_builder(process_class, inputs)
        process = _create_process(process_class, self, input_args=args, input_kwargs=inputs)

        if self._rmq_submit:
            self.persister.save_checkpoint(process)
            process.close()
            self.rmq.continue_process(process.pid)
        else:
            # Run in this runner
            process.start()

        return process.calc

    def _run(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        process, inputs = _expand_builder(process, inputs)

        if utils.is_workfunction(process):
            result, node = process.run_get_node(*args, **inputs)
            return result, node
        else:
            with self.child_runner() as runner:
                process = _ensure_process(process, runner, input_args=args, input_kwargs=inputs)
                return process.execute(), process.calc

    def run(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: the outputs of the process 
        """
        result, node = self._run(process, *args, **inputs)
        return result

    def run_get_node(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and the calculation node
        """
        result, node = self._run(process, *args, **inputs)
        return ResultAndNode(result, node)

    def run_get_pid(self, process, *args, **inputs):
        """
        Run the process with the supplied inputs in this runner that will block until the process is completed.
        The return value will be the results of the completed process

        :param process: the process class or workfunction to run
        :param inputs: the inputs to be passed to the process
        :return: tuple of the outputs of the process and process pid
        """
        result, node = self._run(process, *args, **inputs)
        return ResultAndPid(result, node.pk)

    def call_on_legacy_workflow_finish(self, pk, callback):
        legacy_wf = aiida.orm.load_workflow(pk=pk)
        self._poll_legacy_wf(legacy_wf, callback)

    def call_on_calculation_finish(self, pk, callback):
        calc_node = aiida.orm.load_node(pk=pk)
        self._poll_calculation(calc_node, callback)

    def get_calculation_future(self, pk):
        """
        Get a future for an orm Calculation.  The future will have the calculation node
        as the result when finished.

        :return: A future representing the completion of the calculation node
        """
        return futures.CalculationFuture(
            pk, self._loop, self._poll_interval, self._communicator)

    @contextmanager
    def child_runner(self):
        runner = self._create_child_runner()
        try:
            yield runner
        finally:
            runner.close()

    def _setup_rmq(self, url, prefix=None, task_prefetch_count=None, testing_mode=False):
        self._rmq_connector = plumpy.rmq.RmqConnector(amqp_url=url, loop=self._loop)

        self._rmq_communicator = plumpy.rmq.RmqCommunicator(
            self._rmq_connector,
            exchange_name=rmq.get_message_exchange_name(prefix),
            task_queue=rmq.get_launch_queue_name(prefix),
            testing_mode=testing_mode,
            task_prefetch_count=task_prefetch_count
        )

        self._rmq = rmq.ProcessControlPanel(
            prefix=prefix,
            rmq_connector=self._rmq_connector,
            testing_mode=testing_mode)
        self._communicator = self._rmq._communicator

        # Establish RMQ connection
        self._communicator.connect()

    def _create_child_runner(self):
        return Runner(**self._kwargs)

    def _poll_legacy_wf(self, workflow, callback):
        if workflow.has_finished_ok() or workflow.has_failed():
            self._loop.add_callback(callback, workflow.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_legacy_wf, workflow, callback)

    def _poll_calculation(self, calc_node, callback):
        if calc_node.is_terminated:
            self._loop.add_callback(callback, calc_node.pk)
        else:
            self._loop.call_later(self._poll_interval, self._poll_calculation, calc_node, callback)


class DaemonRunner(Runner):
    """ Overwrites some of the behaviour of a runner to be daemon specific"""

    def __init__(self, *args, **kwargs):
        kwargs['rmq_submit'] = True
        super(DaemonRunner, self).__init__(*args, **kwargs)

    def _setup_rmq(self, url, prefix=None, task_prefetch_count=None, testing_mode=False):
        super(DaemonRunner, self)._setup_rmq(url, prefix, task_prefetch_count, testing_mode)

        # Create a context for loading new processes
        load_context = plumpy.LoadContext(runner=self)

        # Listen for incoming launch requests
        task_receiver = rmq.ProcessLauncher(
            loop=self.loop,
            persister=self.persister,
            load_context=load_context,
            class_loader=class_loader.CLASS_LOADER
        )
        self.communicator.add_task_subscriber(task_receiver)

def _expand_builder(process_class_or_builder, inputs):
    from aiida.work.process_builder import ProcessBuilder
    if not isinstance(process_class_or_builder, ProcessBuilder):
        return process_class_or_builder, inputs
    else:
        builder = process_class_or_builder
        process_class = builder._process_class
        inputs.update(builder._todict())
        return process_class, inputs
