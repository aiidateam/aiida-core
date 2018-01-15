import json
import plum

from aiida.utils.serialize import serialize_data, deserialize_data
from plum import rmq

from . import events

_MESSAGE_EXCHANGE = 'messages'
_LAUNCH_QUEUE = 'process.queue'


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


def create_communicator():
    pass


def get_message_exchange_name(prefix):
    return "{}.{}".format(prefix, _MESSAGE_EXCHANGE)


class ProcessControlPanel(object):
    """
    RMQ control panel for launching, controlling and getting status of
    Processes over the RMQ protocol.
    """

    def __init__(self, prefix, rmq_connector, testing_mode=False):
        self._connector = rmq_connector

        message_exchange = get_message_exchange_name(prefix)
        self.communicator = plum.rmq.RmqCommunicator(
            rmq_connector,
            exchange_name=message_exchange)

        task_queue_name = "{}.{}".format(prefix, _LAUNCH_QUEUE)
        self._launch = rmq.launch.ProcessLaunchPublisher(
            self._connector,
            exchange_name=get_message_exchange_name(prefix),
            task_queue_name=task_queue_name,
            testing_mode=testing_mode
        )

    def ready_future(self):
        return plum.gather(
            self._launch.initialised_future(),
            self.communicator.initialised_future())

    def pause_process(self, pid):
        return self.communicator.rpc_send(pid, plum.PAUSE_MSG)

    def play_process(self, pid):
        return self.communicator.rpc_send(pid, plum.PLAY_MSG)

    def kill_process(self, pid, msg=None):
        return self.communicator.rpc_send(pid, plum.CANCEL_MSG)

    def request_status(self, pid):
        return self.communicator.rpc_send(pid, plum.STATUS_MSG)

    @property
    def launch(self):
        return self._launch


class BlockingProcessControlPanel(object):
    """
    A blocking adapter for the ProcessControlPanel.
    """
    class _Launcher(object):
        def __init__(self, parent):
            self._parent = parent

        def launch_process(self, process_class, init_args=None, init_kwargs=None):
            future = self._parent._control_panel.launch.launch_process(process_class, init_args, init_kwargs)
            return self._parent._run(future)

        def continue_process(self, pid, tag=None):
            future = self._parent._control_panel.launch.continue_process(pid, tag)
            return self._parent._run(future)

    def __init__(self, prefix, rmq_config=None, testing_mode=False):
        if rmq_config is None:
            rmq_config = {
                'url': 'amqp://localhost',
                'prefix': 'aiida',
            }

        self._loop = events.new_event_loop()
        self._connector = plum.rmq.RmqConnector(amqp_url=rmq_config['url'], loop=self._loop)
        self._control_panel = ProcessControlPanel(prefix, self._connector, testing_mode)
        self.launch = self._Launcher(self)

        self._connector.connect()

    def pause_process(self, pid):
        future = self._control_panel.pause_process(pid)
        return self._run(future)

    def play_process(self, pid):
        future = self._control_panel.pause_process(pid)
        return self._run(future)

    def kill_process(self, pid, msg=None):
        future = self._control_panel.kill_process(pid, msg)
        return self._run(future)

    def request_status(self, pid):
        future = self._control_panel.request_status(pid)
        return self._run(future)

    def _run(self, future):
        return events.run_until_complete(future, self._loop)
