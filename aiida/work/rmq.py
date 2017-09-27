import pika
import pika.exceptions
import json
import uuid

from plum import rmq
from aiida.orm import load_node, Node

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


def encode_launch_task(task):
    """
    Convert any AiiDA data types in the task dictionary to PKs and then return
    as JSON string

    :param task: The task dictionary to encode
    :type task: dict
    :return: The JSON string representing the task
    :rtype: str
    """
    task_ = task.copy()
    for name, input in task_.get('input', {}):
        if isinstance(input, Node):
            task_['input'][name] = input.pk
    return json.dumps(task_)


def launch_decode(msg):
    task = json.loads(msg)
    for name, input in task.get('input', {}):
        if isinstance(input, int):
            try:
                task['input'][name] = load_node(pk=input)
            except ValueError:
                pass
    return task


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
        persistent_uuid=_LAUNCH_SUBSCRIBER_UUID
    )


def insert_all_subscribers(loop, prefix, get_connection=_create_connection):
    connection = get_connection()
    get_conn = lambda: connection

    insert_process_control_subscriber(loop, prefix, get_conn)
    insert_process_status_subscriber(loop, prefix, get_conn)
    insert_process_launch_subscriber(loop, prefix, get_conn)


class ProcessControlPanel(object):
    """
    A separate thread for the RabbitMQ related classes.  It's done like this
    because pika requires that the RMQ connection is on the same thread as
    the polling functions so I create them all here and let it poll.
    """

    def __init__(self, loop, prefix, create_connection=_create_connection):
        self.daemon = True

        self._connection = create_connection()

        self._control = loop.create(
            rmq.control.ProcessControlPublisher,
            self._connection,
            "{}.{}".format(prefix, _CONTROL_EXCHANGE)
        )

        self._status = loop.create(
            rmq.status.ProcessStatusRequester,
            self._connection,
            "{}.{}".format(prefix, _STATUS_REQUEST_EXCHANGE),
            status_decode
        )

        self._launch = loop.create(
            rmq.launch.ProcessLaunchPublisher,
            self._connection,
            "{}.{}".format(prefix, _LAUNCH_QUEUE),
            encode_launch_task
        )

    @property
    def control(self):
        return self._control

    @property
    def status(self):
        return self._status

    @property
    def launch(self):
        return self._launch
