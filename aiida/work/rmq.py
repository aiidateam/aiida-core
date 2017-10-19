import apricotpy
import collections
import pika
import pickle
import json
import uuid

from plum import rmq
from plum.utils import override, load_class, fullname
from aiida.orm import load_node, Node
from aiida.work.class_loader import _CLASS_LOADER
from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.common.exceptions import MultipleObjectsError, NotExistent
from aiida.common.setup import get_profile_config, RMQ_PREFIX_KEY
from aiida.backends import settings

_CONTROL_EXCHANGE = 'process.control'
_EVENT_EXCHANGE = 'process.event'
_LAUNCH_QUEUE = 'process.queue'
_STATUS_REQUEST_EXCHANGE = 'process.status_request'
_LAUNCH_SUBSCRIBER_UUID = uuid.UUID('0b8ddfc3-f3cc-49f1-a44f-8418e2ac7e20')

def _create_connection():
    # Set up communications
    try:
        return pika.BlockingConnection()
    except pika.exceptions.ConnectionClosed:
        raise RuntimeError("Couldn't open connection.  Make sure rmq server is running")

def _get_prefix():
    """Get the queue prefix from the profile."""
    return 'aiida-' + get_profile_config(settings.AIIDADB_PROFILE)[RMQ_PREFIX_KEY]

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


def insert_process_control_subscriber(loop, get_prefix=_get_prefix, get_connection=_create_connection):
    return loop.create(
        rmq.control.ProcessControlSubscriber,
        get_connection(),
        "{}.{}".format(_get_prefix(), _CONTROL_EXCHANGE),
    )

def insert_process_status_subscriber(loop, get_prefix=_get_prefix, get_connection=_create_connection):
    return loop.create(
        rmq.status.ProcessStatusSubscriber,
        get_connection(),
        "{}.{}".format(_get_prefix(), _STATUS_REQUEST_EXCHANGE),
    )

def insert_process_launch_subscriber(loop, get_prefix=_get_prefix, get_connection=_create_connection):
    return loop.create(
        rmq.launch.ProcessLaunchSubscriber,
        get_connection(),
        "{}.{}".format(_get_prefix(), _LAUNCH_QUEUE),
        response_encoder=encode_response
    )

def insert_all_subscribers(loop, get_prefix=_get_prefix, get_connection=_create_connection):
    # Give them all the same connection instance
    connection = get_connection()
    get_conn = lambda: connection

    prefix = _get_prefix()
    insert_process_control_subscriber(loop, prefix, get_conn)
    insert_process_status_subscriber(loop, prefix, get_conn)
    insert_process_launch_subscriber(loop, prefix, get_conn)

class ProcessControlPanel(apricotpy.LoopObject):
    """
    RMQ control panel for launching, controlling and getting status of
    Processes over the RMQ protocol.
    """

    def __init__(self, get_prefix=_get_prefix, create_connection=_create_connection):
        super(ProcessControlPanel, self).__init__()

        self._prefix = get_prefix()
        self._connection = create_connection()

        self._control = rmq.control.ProcessControlPublisher(
            self._connection,
            "{}.{}".format(self._prefix, _CONTROL_EXCHANGE)
        )

        self._status = rmq.status.ProcessStatusRequester(
            self._connection,
            "{}.{}".format(self._prefix, _STATUS_REQUEST_EXCHANGE),
            status_decode
        )

        self._launch = rmq.launch.ProcessLaunchPublisher(
            self._connection,
            "{}.{}".format(self._prefix, _LAUNCH_QUEUE),
            pickle.dumps,
            decode_response
        )

    def on_loop_inserted(self, loop):
        super(ProcessControlPanel, self).on_loop_inserted(loop)
        loop._insert(self._control)
        loop._insert(self._status)
        loop._insert(self._launch)

    def on_loop_removed(self):
        loop = self.loop()
        loop._remove(self._control)
        loop._remove(self._status)
        loop._remove(self._launch)
        super(ProcessControlPanel, self).on_loop_removed()

    @property
    def control(self):
        return self._control

    @property
    def status(self):
        return self._status

    def launch(self, process_bundle):
        return self._launch.launch(process_bundle)


def create_control_panel(get_prefix=_get_prefix, create_connection=_create_connection):
    return ProcessControlPanel(
        get_prefix=get_prefix,
        create_connection=create_connection
    )
