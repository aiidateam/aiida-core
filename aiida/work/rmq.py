import json
import plum
import plum.rmq

from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.common.setup import get_profile_config, RMQ_PREFIX_KEY
from aiida.backends import settings

from . import events

__all__ = ['new_blocking_control_panel', 'BlockingProcessControlPanel',
           'RemoteException', 'DeliveryFailed', 'ProcessLauncher']

RemoteException = plum.RemoteException
DeliveryFailed = plum.DeliveryFailed

_MESSAGE_EXCHANGE = 'messages'
_LAUNCH_QUEUE = 'process.queue'


def _get_prefix():
    """Get the queue prefix from the profile."""
    return 'aiida-' + get_profile_config(settings.AIIDADB_PROFILE)[RMQ_PREFIX_KEY]


def _get_rmq_config():
    rmq_config = {
        'url': 'amqp://localhost',
        'prefix': _get_prefix(),
    }
    return rmq_config


def encode_response(response):
    serialized = serialize_data(response)
    return json.dumps(serialized)


def decode_response(response):
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


class LaunchProcessAction(plum.LaunchProcessAction):

    def __init__(self, *args, **kwargs):
        """
        Calls through to the constructor of the plum LaunchProcessAction while making sure that
        any unstored nodes in the inputs are first stored and the data is then serialized
        """
        kwargs['inputs'] = store_and_serialize_inputs(kwargs['inputs'])
        super(LaunchProcessAction, self).__init__(*args, **kwargs)


class ExecuteProcessAction(plum.ExecuteProcessAction):

    def __init__(self, process_class, init_args=None, init_kwargs=None):
        """
        Calls through to the constructor of the plum ExecuteProcessAction while making sure that
        any unstored nodes in the inputs are first stored and the data is then serialized
        """
        init_kwargs['inputs'] = store_and_serialize_inputs(init_kwargs['inputs'])
        super(ExecuteProcessAction, self).__init__(process_class, init_args, init_kwargs)


class ProcessLauncher(plum.ProcessLauncher):

    def _launch(self, task):
        from plum.process_comms import KWARGS_KEY
        kwargs = task.get(KWARGS_KEY, {})
        kwargs['inputs'] = deserialize_data(kwargs['inputs'])
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
        self._communicator = plum.rmq.RmqCommunicator(
            rmq_connector,
            exchange_name=message_exchange,
            task_queue=task_queue,
            blocking_mode=False,
            testing_mode=testing_mode
        )

    def ready_future(self):
        return self._communicator.initialised_future()

    def pause_process(self, pid):
        return self.execute_action(plum.PauseAction(pid))

    def play_process(self, pid):
        return self.execute_action(plum.PlayAction(pid))

    def kill_process(self, pid, msg=None):
        return self.execute_action(plum.CancelAction(pid))

    def request_status(self, pid):
        return self.execute_action(plum.StatusAction(pid))

    def launch_process(self, process_class, init_args=None, init_kwargs=None):
        action = LaunchProcessAction(process_class, init_args, init_kwargs)
        action.execute(self._communicator)
        return action

    def continue_process(self, pid):
        action = plum.ContinueProcessAction(pid)
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
        self._loop = events.new_event_loop()
        connector = new_rmq_connector(self._loop)
        super(BlockingProcessControlPanel, self).__init__(prefix, connector, testing_mode)

        self._connector.connect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute_process_start(self, process_class, init_args=None, init_kwargs=None):
        action = ExecuteProcessAction(process_class, init_args, init_kwargs)
        action.execute(self._communicator)
        events.run_until_complete(action, self._loop)
        return action.get_launch_future().result()

    def execute_action(self, action):
        action.execute(self._communicator)
        return events.run_until_complete(action, self._loop)

    def close(self):
        self._connector.close()


def new_blocking_control_panel():
    """
    Create a new blocking control panel based on the current profile configuration

    :return: A new control panel instance
    :rtype: :class:`BlockingProcessControlPanel`
    """
    return BlockingProcessControlPanel(_get_prefix())


def new_rmq_connector(loop):
    return plum.rmq.RmqConnector(amqp_url=_get_rmq_config()['url'], loop=loop)
