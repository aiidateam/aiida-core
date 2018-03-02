import json
import plumpy
import plumpy.rmq

from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.common.setup import get_profile_config, PROFILE_UUID_KEY
from aiida.backends import settings
from aiida.work.class_loader import CLASS_LOADER

__all__ = ['new_blocking_control_panel', 'BlockingProcessControlPanel',
           'RemoteException', 'DeliveryFailed', 'ProcessLauncher']

RemoteException = plumpy.RemoteException
DeliveryFailed = plumpy.DeliveryFailed

_MESSAGE_EXCHANGE = 'messages'
_LAUNCH_QUEUE = 'process.queue'


def _get_prefix():
    """Get the queue prefix from the profile."""
    return 'aiida-' + get_profile_config(settings.AIIDADB_PROFILE)[PROFILE_UUID_KEY]


def get_rmq_config(prefix=None):
    if prefix is None:
        prefix = _get_prefix()

    # GP: Using here 127.0.0.1 instead of localhost because on some computers
    # localhost resolves first to IPv6 with address ::1 and if RMQ is not
    # running on IPv6 one gets an annoying warning. When moving this to
    # a user-configurable variable, make sure users are aware of this and
    # know how to avoid warnings. For more info see
    # https://github.com/aiidateam/aiida_core/issues/1142
    rmq_config = {
        'url': 'amqp://127.0.0.1',
        'prefix': _get_prefix(),
    }
    return rmq_config


def encode_response(response):
    """
    Used by kiwipy to encode a message for sending.  Because we can have nodes
    we have to convert these to PIDs before sending (we can't just send the live
    instance)

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


def get_launch_queue_name(prefix=None):
    if prefix is not None:
        return "{}.{}".format(prefix, _LAUNCH_QUEUE)

    return _LAUNCH_QUEUE


def get_message_exchange_name(prefix):
    return "{}.{}".format(prefix, _MESSAGE_EXCHANGE)


def store_and_serialize_inputs(inputs):
    """
    Iterate over the values of the input dictionary, try to store them as if they were unstored
    nodes and then return the serialized dictionary

    :param inputs: dictionary where keys are potentially unstored node instances
    :returns: a dictionary where nodes are serialized
    """
    for node in inputs.itervalues():
        try:
            node.store()
        except AttributeError:
            pass
    return serialize_data(inputs)


class LaunchProcessAction(plumpy.LaunchProcessAction):
    def __init__(self, *args, **kwargs):
        """
        Calls through to the constructor of the plum LaunchProcessAction while making sure that
        any unstored nodes in the inputs are first stored and the data is then serialized
        """
        kwargs['inputs'] = store_and_serialize_inputs(kwargs['inputs'])
        kwargs['class_loader'] = CLASS_LOADER
        super(LaunchProcessAction, self).__init__(*args, **kwargs)


class ExecuteProcessAction(plumpy.ExecuteProcessAction):
    def __init__(self, process_class, init_args=None, init_kwargs=None, nowait=False):
        """
        Calls through to the constructor of the plum ExecuteProcessAction while making sure that
        any unstored nodes in the inputs are first stored and the data is then serialized
        """
        init_kwargs['inputs'] = store_and_serialize_inputs(init_kwargs['inputs'])
        super(ExecuteProcessAction, self).__init__(process_class, init_args, init_kwargs, class_loader=CLASS_LOADER, nowait=nowait)


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
        task_queue = get_launch_queue_name(prefix)
        self._communicator = plumpy.rmq.RmqCommunicator(
            rmq_connector,
            exchange_name=message_exchange,
            task_queue=task_queue,
            encoder=encode_response,
            decoder=decode_response,
            testing_mode=testing_mode
        )

    def connect(self):
        return self._communicator.init()

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
        self._loop = plumpy.new_event_loop()
        connector = create_rmq_connector(self._loop)
        super(BlockingProcessControlPanel, self).__init__(prefix, connector, testing_mode)

        self.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute_process_start(self, process_class, init_args=None, init_kwargs=None):
        action = ExecuteProcessAction(process_class, init_args, init_kwargs, nowait=True)
        action.execute(self._communicator)
        self._communicator.await(action)
        return action.get_launch_future().result()

    def execute_action(self, action):
        action.execute(self._communicator)
        return self._communicator.await(action)

    def close(self):
        self._communicator.disconnect()


def new_blocking_control_panel():
    """
    Create a new blocking control panel based on the current profile configuration

    :return: A new control panel instance
    :rtype: :class:`BlockingProcessControlPanel`
    """
    return BlockingProcessControlPanel(_get_prefix())


def create_rmq_connector(loop=None):
    if loop is None:
        loop = events.new_event_loop()
    return plumpy.rmq.RmqConnector(amqp_url=get_rmq_config()['url'], loop=loop)


def create_communicator(loop=None, prefix=None, testing_mode=False):
    if prefix is None:
        prefix = _get_prefix()

    message_exchange = get_message_exchange_name(prefix)
    task_queue = get_launch_queue_name(prefix)

    connector = create_rmq_connector(loop)
    return plumpy.rmq.RmqCommunicator(
        connector,
        exchange_name=message_exchange,
        task_queue=task_queue,
        testing_mode=testing_mode
    )
