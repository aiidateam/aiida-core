import apricotpy
import collections
import pika
import pika.exceptions
import json
import uuid

from ast import literal_eval
from plum import rmq
from plum.utils import override, load_class, fullname
from aiida.orm import load_node, Node
from aiida.work.class_loader import _CLASS_LOADER
from aiida.common.exceptions import MultipleObjectsError, NotExistent

_CONTROL_EXCHANGE = 'process.control'
_EVENT_EXCHANGE = 'process.event'
_LAUNCH_QUEUE = 'process.queue'
_STATUS_REQUEST_EXCHANGE = 'process.status_request'
_LAUNCH_SUBSCRIBER_UUID = uuid.UUID('0b8ddfc3-f3cc-49f1-a44f-8418e2ac7e20')
_PREFIX_LABEL_TUPLE = 'tuple():'
_PREFIX_VALUE_NODE = 'aiida_node:'

def _create_connection():
    # Set up communications
    try:
        return pika.BlockingConnection()
    except pika.exceptions.ConnectionClosed:
        raise RuntimeError("Couldn't open connection.  Make sure rmq server is running")

def serialize_mapping(mapping):
    """
    """
    serialized = {}
    for label, value in mapping.iteritems():

        if isinstance(label, tuple):
            label = '{}{}'.format(_PREFIX_LABEL_TUPLE, label)

        if isinstance(value, collections.Mapping):
            serialized[label] = serialize_mapping(value)
        elif isinstance(value, Node):
            if not value.is_stored:
                value.store()
            serialized[label] = '{}{}'.format(_PREFIX_VALUE_NODE, value.uuid)
        else:
            serialized[label] = value

    return serialized

def deserialize_mapping(mapping):
    """
    """
    deserialized = {}
    for label, value in mapping.iteritems():

        if label.startswith(_PREFIX_LABEL_TUPLE):
            label = literal_eval(label[len(_PREFIX_LABEL_TUPLE):])

        if isinstance(value, collections.Mapping):
            deserialized[label] = deserialize_mapping(value)
        elif isinstance(value, unicode) and value.startswith(_PREFIX_VALUE_NODE):
            node_uuid = value[len(_PREFIX_VALUE_NODE):]
            deserialized[label] = load_node(uuid=node_uuid)
        else:
            deserialized[label] = value

    return deserialized


def encode_launch_task(proc_class, *args, **kwargs):
    """
    Convert any AiiDA data types in the task dictionary to PKs and then return
    as JSON string

    :param task: The task dictionary to encode
    :type task: dict
    :return: The JSON string representing the task
    :rtype: str
    """
    serialized = {
        'proc_class': fullname(proc_class),
        'args': args,
        'kwargs': serialize_mapping(kwargs)
    }
    return json.dumps(serialized)

def decode_launch_task(serialized_task):
    """
    """
    task = json.loads(serialized_task)
    proc_class = _CLASS_LOADER.load_class(task['proc_class'])
    args = task['args']
    kwargs = deserialize_mapping(task['kwargs'])
    task = rmq.launch._TaskInfo(proc_class, args, kwargs)
    return task

def encode_response(mapping):
    return json.dumps(serialize_mapping(mapping))

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


def insert_process_control_subscriber(loop, prefix, get_connection=_create_connection):
    return loop.create(
        rmq.control.ProcessControlSubscriber,
        get_connection(),
        "{}.{}".format(prefix, _CONTROL_EXCHANGE),
    )


def insert_process_status_subscriber(loop, prefix, get_connection=_create_connection):
    return loop.create(
        rmq.status.ProcessStatusSubscriber,
        get_connection(),
        "{}.{}".format(prefix, _STATUS_REQUEST_EXCHANGE),
    )


def insert_process_launch_subscriber(loop, prefix, get_connection=_create_connection):
    return loop.create(
        rmq.launch.ProcessLaunchSubscriber,
        get_connection(),
        "{}.{}".format(prefix, _LAUNCH_QUEUE),
        decode_launch_task,
        encode_response
    )


def insert_all_subscribers(loop, prefix, get_connection=_create_connection):
    # Give them all the same connection instance
    connection = get_connection()
    get_conn = lambda: connection

    insert_process_control_subscriber(loop, prefix, get_conn)
    insert_process_status_subscriber(loop, prefix, get_conn)
    insert_process_launch_subscriber(loop, prefix, get_conn)


class ProcessControlPanel(apricotpy.LoopObject):
    """
    RMQ control panel for launching, controlling and getting status of
    Processes over the RMQ protocol.
    """

    def __init__(self, prefix, create_connection=_create_connection):
        super(ProcessControlPanel, self).__init__()

        self._connection = create_connection()

        self._control = rmq.control.ProcessControlPublisher(
            self._connection,
            "{}.{}".format(prefix, _CONTROL_EXCHANGE)
        )

        self._status = rmq.status.ProcessStatusRequester(
            self._connection,
            "{}.{}".format(prefix, _STATUS_REQUEST_EXCHANGE),
            status_decode
        )

        self._launch = rmq.launch.ProcessLaunchPublisher(
            self._connection,
            "{}.{}".format(prefix, _LAUNCH_QUEUE),
            encode_launch_task
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

    def launch(self, process_class, inputs=None):
        return self._launch.launch(process_class, inputs)


def create_control_panel(prefix="aiida", create_connection=_create_connection):
    return ProcessControlPanel(prefix, create_connection)
