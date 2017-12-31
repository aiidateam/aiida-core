import json
import pickle
import pika
import uuid

from aiida.utils.serialize import serialize_data, deserialize_data
from plum import rmq

_CONTROL_EXCHANGE = 'process.control'
_EVENT_EXCHANGE = 'process.event'
_LAUNCH_QUEUE = 'process.queue'
_STATUS_REQUEST_EXCHANGE = 'process.status_request'
_LAUNCH_SUBSCRIBER_UUID = uuid.UUID('0b8ddfc3-f3cc-49f1-a44f-8418e2ac7e20')


def encode_response(response):
    serialized = serialize_data(response)
    return json.dumps(serialized)


def decode_response(response):
    response = json.loads(response)
    return deserialize_data(response)


def status_decode(msg):
    decoded = rmq.status.status_decode(msg)
    # Just need to fix up the special case of PIDs being PKs (i.e. ints)
    procs = decoded[rmq.status.PROCS_KEY]
    for pid in procs.keys():
        try:
            if not isinstance(pid, uuid.UUID):
                new_pid = int(pid)
                procs[new_pid] = procs.pop(pid)
        except ValueError:
            pass
    return decoded


def get_launch_queue_name(prefix=None):
    if prefix is not None:
        return "{}.{}".format(prefix, _LAUNCH_QUEUE)

    return _LAUNCH_QUEUE


class ProcessControlPanel(object):
    """
    RMQ control panel for launching, controlling and getting status of
    Processes over the RMQ protocol.
    """

    def __init__(self, prefix, rmq_connector, testing_mode=False):
        self._connector = rmq_connector

        # self._control = rmq.control.ProcessControlPublisher(
        #     self._connection,
        #     "{}.{}".format(prefix, _CONTROL_EXCHANGE)
        # )
        #
        # self._status = rmq.status.ProcessStatusRequester(
        #     self._connection,
        #     "{}.{}".format(prefix, _STATUS_REQUEST_EXCHANGE),
        #     status_decode
        # )

        launch_queue_name = "{}.{}".format(prefix, _LAUNCH_QUEUE)
        self._launch = rmq.launch.ProcessLaunchPublisher(
            self._connector,
            queue_name=launch_queue_name, testing_mode=testing_mode
        )

    #
    # @property
    # def control(self):
    #     return self._control
    #
    # @property
    # def status(self):
    #     return self._status

    @property
    def launch(self):
        return self._launch
