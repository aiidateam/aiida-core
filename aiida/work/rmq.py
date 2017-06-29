import pika
import pika.exceptions
import json
import uuid

import plum.rmq.control
import plum.rmq.event
import plum.rmq.launch
from plum.rmq.util import SubscriberThread
import plum.rmq
import plum.rmq.status
from aiida.orm import load_node, Node

_CONTROL_EXCHANGE = 'process.control'
_EVENT_EXCHANGE = 'process.event'
_LAUNCH_QUEUE = 'process.queue'
_STATUS_REQUEST_EXCHANGE = 'process.status_request'


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
    decoded = plum.rmq.status.status_decode(msg)
    # Just need to fix up the special case of PIDs being PKs (i.e. ints)
    procs = decoded[plum.rmq.status.PROCS_KEY]
    for pid in procs.keys():
        try:
            if not isinstance(pid, uuid.UUID):
                new_pid = int(pid)
                procs[new_pid] = procs.pop(pid)
        except ValueError:
            pass
    return decoded


def _create_subscribers(procman, prefix, connection):
    subs = [

        plum.rmq.ProcessControlSubscriber(
            connection=connection, exchange=".".join([prefix, _CONTROL_EXCHANGE]),
            process_controller=procman
        ),

        plum.rmq.ProcessLaunchSubscriber(
            connection=connection, queue=".".join([prefix, _LAUNCH_QUEUE]),
            process_controller=procman
        ),

        plum.rmq.ProcessStatusSubscriber(
            connection=connection, process_controller=procman,
            exchange=".".join([prefix, _STATUS_REQUEST_EXCHANGE])
        ),
    ]

    return subs


def enable_subscribers(procman, prefix):
    """
    Enable RMQ subscribers for the process manager.  This means that RMQ
    launch, status and control messages will be listened for and processed.
    """
    from functools import partial
    create_subscribers = partial(_create_subscribers, procman, prefix)
    thread = SubscriberThread(
        _create_connection, create_subscribers, name="rmq_subscriber.{}".format(prefix)
    )
    thread.start()
    return thread


_GLOBAL_EVENT_PUBLISHER = None


def enable_process_event_publisher():
    global _GLOBAL_EVENT_PUBLISHER
    if _GLOBAL_EVENT_PUBLISHER is None:
        _GLOBAL_EVENT_PUBLISHER = \
            plum.rmq.event.ProcessEventPublisher(
                _create_connection(), exchange=_EVENT_EXCHANGE)
    _GLOBAL_EVENT_PUBLISHER.enable_publish_all()


def disable_process_event_publisher():
    global _GLOBAL_EVENT_PUBLISHER
    if _GLOBAL_EVENT_PUBLISHER is not None:
        _GLOBAL_EVENT_PUBLISHER.disable_publish_all()


def create_process_event_listener():
    return plum.rmq.event.ProcessEventSubscriber(
        _create_connection(), exchange=_EVENT_EXCHANGE)


class ProcessControlPanel(object):
    """
    A separate thread for the RabbitMQ related classes.  It's done like this
    because pika requires that the RMQ connection is on the same thread as
    the polling functions so I create them all here and let it poll.
    """

    def __init__(self, prefix, create_connection=_create_connection):
        self.daemon = True

        self._connection = create_connection()

        self._control = plum.rmq.ProcessControlPublisher(
            connection=self._connection,
            exchange=".".join([prefix, _CONTROL_EXCHANGE])
        )

        self._status = plum.rmq.ProcessStatusRequester(
            connection=self._connection,
            exchange=".".join([prefix, _STATUS_REQUEST_EXCHANGE]),
            decoder=status_decode
        )

        self._launch = plum.rmq.ProcessLaunchPublisher(
            connection=self._connection,
            queue=".".join([prefix, _LAUNCH_QUEUE]),
            encoder=encode_launch_task
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
