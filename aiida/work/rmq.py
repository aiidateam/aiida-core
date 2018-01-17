import json
import plum
import uuid

from aiida.utils.serialize import serialize_data, deserialize_data

from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.common.setup import get_profile_config, RMQ_PREFIX_KEY
from aiida.backends import settings
from plum import rmq

_MESSAGE_EXCHANGE = 'messages'
_LAUNCH_QUEUE = 'process.queue'


def _get_prefix():
    """Get the queue prefix from the profile."""
    return 'aiida-' + get_profile_config(settings.AIIDADB_PROFILE)[RMQ_PREFIX_KEY]

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