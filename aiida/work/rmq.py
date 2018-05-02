# -*- coding: utf-8 -*-
import json
import collections
import plumpy
import plumpy.rmq
import tornado.ioloop

from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.work.persistence import AiiDAPersister

from . import persistence
from . import utils

__all__ = ['new_control_panel', 'new_blocking_control_panel', 'BlockingProcessControlPanel',
           'RemoteException', 'DeliveryFailed', 'ProcessLauncher', 'ProcessControlPanel']

RemoteException = plumpy.RemoteException
DeliveryFailed = plumpy.DeliveryFailed

# GP: Using here 127.0.0.1 instead of localhost because on some computers
# localhost resolves first to IPv6 with address ::1 and if RMQ is not
# running on IPv6 one gets an annoying warning. When moving this to
# a user-configurable variable, make sure users are aware of this and
# know how to avoid warnings. For more info see
# https://github.com/aiidateam/aiida_core/issues/1142
_RMQ_URL = 'amqp://127.0.0.1'
_RMQ_TASK_PREFETCH_COUNT = 20
_RMQ_HEARTBEAT_TIMEOUT = 600
_LAUNCH_QUEUE = 'process.queue'
_MESSAGE_EXCHANGE = 'messages'
_TASK_EXCHANGE = 'tasks'


def get_rmq_url(heartbeat_timeout=None):
    """
    Get the URL to connect to RabbitMQ

    :param heartbeat_timeout: the interval in seconds for the heartbeat timeout
    :returns: the connection URL string
    """
    url = _RMQ_URL

    if heartbeat_timeout is None:
        heartbeat_timeout = _RMQ_HEARTBEAT_TIMEOUT

    if heartbeat_timeout is not None:
        url += '?heartbeat={}'.format(heartbeat_timeout)

    return url


def get_rmq_prefix():
    """
    Get the prefix for the RabbitMQ message queues and exchanges for the current profile

    :returns: string prefix for the RMQ communicators
    """
    from aiida.common.profile import ProfileConfig

    profile_config = ProfileConfig()
    prefix = profile_config.rmq_prefix

    return prefix


def get_rmq_config(prefix=None):
    """
    Get the RabbitMQ configuration dictionary for a given prefix. If the prefix is not
    specified, the prefix will be retrieved from the currently loaded profile configuration

    :param prefix: a string prefix for the RabbitMQ communication queues and exchanges
    :returns: the configuration dictionary for the RabbitMQ communicators
    """
    if prefix is None:
        prefix = get_rmq_prefix()

    rmq_config = {
        'url': get_rmq_url(),
        'prefix': prefix,
        'task_prefetch_count': _RMQ_TASK_PREFETCH_COUNT
    }

    return rmq_config


def get_launch_queue_name(prefix=None):
    """
    Return the launch queue name with an optional prefix

    :returns: launch queue name
    """
    if prefix is not None:
        return '{}.{}'.format(prefix, _LAUNCH_QUEUE)

    return _LAUNCH_QUEUE


def get_message_exchange_name(prefix):
    """
    Return the message exchange name for a given prefix

    :returns: message exchange name
    """
    return '{}.{}'.format(prefix, _MESSAGE_EXCHANGE)


def get_task_exchange_name(prefix):
    """
    Return the task exchange name for a given prefix

    :returns: task exchange name
    """
    return '{}.{}'.format(prefix, _TASK_EXCHANGE)


def encode_response(response):
    """
    Used by kiwipy to encode a message for sending.  Because we can have nodes, we have
    to convert these to PIDs before sending (we can't just send the live instance)

    :param response: The message to encode
    :return: The encoded message
    :rtype: str
    """
    serialized = serialize_data(response)
    return json.dumps(serialized)


def decode_response(response):
    """
    Used by kiwipy to decode a message that has been received.  We check for
    any node PKs and convert these back into the corresponding node instance
    using `load_node`.  Any other entries are left untouched.

    .. see: `encode_response`

    :param response: The response string to decode
    :return: A data structure containing deserialized node instances
    """
    response = json.loads(response)
    return deserialize_data(response)


def store_and_serialize_inputs(inputs):
    """
    Iterate over the values of the input dictionary, try to store them as if they were unstored
    nodes and then return the serialized dictionary

    :param inputs: dictionary where keys are potentially unstored node instances
    :returns: a dictionary where nodes are serialized
    """
    _store_inputs(inputs)
    return serialize_data(inputs)


def _store_inputs(inputs):
    """
    Try to store the values in the input dictionary. For nested dictionaries, the values are stored by recursively.
    """
    for node in inputs.values():
        try:
            node.store()
        except AttributeError:
            if isinstance(node, collections.Mapping):
                _store_inputs(node)


class LaunchProcessAction(plumpy.LaunchProcessAction):
    def __init__(self, *args, **kwargs):
        """
        Calls through to the constructor of the plum LaunchProcessAction while making sure that
        any unstored nodes in the inputs are first stored and the data is then serialized
        """
        kwargs['inputs'] = store_and_serialize_inputs(kwargs['inputs'])
        kwargs['class_loader'] = persistence.get_object_loader()
        super(LaunchProcessAction, self).__init__(*args, **kwargs)


class ExecuteProcessAction(plumpy.Action):

    def __init__(self, process_class, init_args=None, init_kwargs=None, nowait=False, persister=None):
        super(ExecuteProcessAction, self).__init__()
        self._process_class = process_class
        self._args = init_args or ()
        self._kwargs = init_kwargs or {}
        self._nowait = nowait

        if persister is not None:
            self._persister = persister
        else:
            self._persister = AiiDAPersister()

    def execute(self, publisher):
        proc = self._process_class(*self._args, **self._kwargs)
        self._persister.save_checkpoint(proc)
        proc.close()

        continue_action = plumpy.ContinueProcessAction(proc.calc.pk, play=True)
        continue_action.execute(publisher)

        self.set_result(proc.calc.pk)


class ProcessLauncher(plumpy.ProcessLauncher):
    def _launch(self, task):
        from plumpy.process_comms import KWARGS_KEY
        kwargs = task.get(KWARGS_KEY, {})
        task[KWARGS_KEY] = kwargs
        return super(ProcessLauncher, self)._launch(task)


class ProcessControlPanel(object):
    """
    RMQ control panel for launching, controlling and getting status of
    Processes over the RMQ protocol.
    """

    def __init__(self, prefix, rmq_connector, testing_mode=False):
        self._connector = rmq_connector

        message_exchange = get_message_exchange_name(prefix)
        task_exchange = get_task_exchange_name(prefix)

        task_queue = get_launch_queue_name(prefix)
        self._communicator = plumpy.rmq.RmqCommunicator(
            rmq_connector,
            exchange_name=message_exchange,
            task_exchange=task_exchange,
            task_queue=task_queue,
            encoder=encode_response,
            decoder=decode_response,
            testing_mode=testing_mode,
            task_prefetch_count=_RMQ_TASK_PREFETCH_COUNT
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._communicator.disconnect()

    def connect(self):
        return self._communicator.connect()

    def pause_process(self, pid):
        return self.execute_action(plumpy.PauseAction(pid))

    def play_process(self, pid):
        return self.execute_action(plumpy.PlayAction(pid))

    def kill_process(self, pid, msg=None):
        return self.execute_action(plumpy.KillAction(pid))

    def request_status(self, pid):
        return self.execute_action(plumpy.StatusAction(pid))

    def launch_process(self, process_class, init_args=None, init_kwargs=None):
        action = LaunchProcessAction(process_class, init_args, init_kwargs)
        action.execute(self._communicator)
        return action

    def continue_process(self, pid):
        action = plumpy.ContinueProcessAction(pid)
        action.execute(self._communicator)
        return action

    def execute_process(self, process_class, init_args=None, init_kwargs=None):
        action = ExecuteProcessAction(process_class, init_args, init_kwargs)
        action.execute(self._communicator)
        return action

    def execute_action(self, action):
        action.execute(self._communicator)
        return action


class BlockingProcessControlPanel(ProcessControlPanel):
    """
    A blocking adapter for the ProcessControlPanel.
    """

    def __init__(self, prefix, testing_mode=False):
        self._loop = tornado.ioloop.IOLoop()
        connector = create_rmq_connector(self._loop)
        super(BlockingProcessControlPanel, self).__init__(prefix, connector, testing_mode)

        self.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._loop.close()
        self.close()

    def execute_process_start(self, process_class, init_args=None, init_kwargs=None):
        action = ExecuteProcessAction(process_class, init_args, init_kwargs, nowait=True)
        action.execute(self._communicator)
        self._communicator.await(action)
        return action.result()

    def execute_action(self, action):
        with utils.loop_scope(self._loop):
            action.execute(self._communicator)
            return self._communicator.await(action)

    def close(self):
        self._communicator.disconnect()


def new_control_panel():
    """
    Create a new control panel based on the current profile configuration

    :return: A new control panel instance
    :rtype: :py:class:`aiida.work.rmq.ProcessControlPanel`
    """
    prefix = get_rmq_prefix()
    connector = create_rmq_connector()
    return ProcessControlPanel(prefix, connector)


def new_blocking_control_panel():
    """
    Create a new blocking control panel based on the current profile configuration

    :return: A new control panel instance
    :rtype: :py:class:`aiida.work.rmq.BlockingProcessControlPanel`
    """
    prefix = get_rmq_prefix()
    return BlockingProcessControlPanel(prefix)


def create_rmq_connector(loop=None):
    if loop is None:
        loop = tornado.ioloop.IOLoop.current()
    return plumpy.rmq.RmqConnector(amqp_url=get_rmq_url(), loop=loop)


def create_communicator(loop=None, prefix=None, testing_mode=False):
    if prefix is None:
        prefix = get_rmq_prefix()

    message_exchange = get_message_exchange_name(prefix)
    task_queue = get_launch_queue_name(prefix)

    connector = create_rmq_connector(loop)
    return plumpy.rmq.RmqCommunicator(
        connector,
        exchange_name=message_exchange,
        task_queue=task_queue,
        testing_mode=testing_mode,
        task_prefetch_count=_RMQ_TASK_PREFETCH_COUNT
    )
