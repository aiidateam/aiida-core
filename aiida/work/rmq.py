# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-few-public-methods
"""Components to communicate tasks to RabbitMQ."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import collections

import yaml

from tornado import gen
import plumpy
import kiwipy.rmq
from kiwipy import communications

from aiida.utils.serialize import serialize_data, deserialize_data
from aiida.work.exceptions import PastException

__all__ = [
    'RemoteException', 'CommunicationTimeout', 'DeliveryFailed', 'ProcessLauncher', 'create_controller',
    'create_communicator'
]

RemoteException = plumpy.RemoteException
DeliveryFailed = plumpy.DeliveryFailed
CommunicationTimeout = communications.TimeoutError  # pylint: disable=invalid-name

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

    rmq_config = {'url': get_rmq_url(), 'prefix': prefix, 'task_prefetch_count': _RMQ_TASK_PREFETCH_COUNT}

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
    return yaml.dump(serialized)


def decode_response(response):
    """
    Used by kiwipy to decode a message that has been received.  We check for
    any node PKs and convert these back into the corresponding node instance
    using `load_node`.  Any other entries are left untouched.

    .. see: `encode_response`

    :param response: The response string to decode
    :return: A data structure containing deserialized node instances
    """
    response = yaml.load(response)
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


class ProcessLauncher(plumpy.ProcessLauncher):
    """
    A sub class of plumpy.ProcessLauncher to launch a Process

    It overrides the _continue method to make sure the node corresponding to the task can be loaded and
    that if it is already marked as terminated, it is not continued but the future is reconstructed and returned
    """

    @gen.coroutine
    def _continue(self, communicator, pid, nowait, tag=None):
        """
        Continue the task

        Note that the task may already have been completed, as indicated from the corresponding the node, in which
        case it is not continued, but the corresponding future is reconstructed and returned. This scenario may
        occur when the Process was already completed by another worker that however failed to send the acknowledgment.

        :param communicator: the communicator that called this method
        :param pid: the pid of the process to continue
        :param nowait: if True don't wait for the process to finish, just return the pid, otherwise wait and
            return the results
        :param tag: the tag of the checkpoint to continue from
        :raises plumpy.TaskRejected: if the node corresponding to the task cannot be loaded
        """
        from aiida.common import exceptions
        from aiida.orm import load_node, Data

        try:
            node = load_node(pk=pid)
        except (exceptions.MultipleObjectsError, exceptions.NotExistent) as exception:
            raise plumpy.TaskRejected('Cannot continue process: {}'.format(exception))

        if node.is_terminated:

            future = communicator.create_future()

            if node.is_finished:
                future.set_result(dict(node.get_outputs(node_type=Data, also_labels=True)))
            elif node.is_excepted:
                future.set_exception(PastException(node.exception))
            elif node.is_killed:
                future.set_exception(plumpy.KilledError())

            raise gen.Return(future.result())

        result = yield super(ProcessLauncher, self)._continue(communicator, pid, nowait, tag)
        raise gen.Return(result)


def create_controller(communicator=None):
    """
    Create a RemoteProcessThreadController

    :param communicator: a :class:`~kiwipy.Communicator`
    :return: a :class:`~plumpy.RemoteProcessThreadController` instance
    """
    if communicator is None:
        communicator = create_communicator()

    return plumpy.RemoteProcessThreadController(communicator=communicator)


def create_communicator(url=None, prefix=None, task_prefetch_count=_RMQ_TASK_PREFETCH_COUNT, testing_mode=False):
    """
    Create a Communicator

    :param prefix: optionally a specific prefix to use for the RMQ connection
    :param testing_mode: whether to create a communicator in testing mode
    :type testing_mode: bool
    :return: the communicator instance
    :rtype: :class:`kiwipy.Communicator`
    """
    from aiida.common.profile import ProfileConfig

    profile_config = ProfileConfig()

    if url is None:
        url = get_rmq_url()

    if prefix is None:
        prefix = get_rmq_prefix()

    # This needs to be here, because the verdi commands will call this function and when called in unit tests the
    # testing_mode cannot be set. Currently the "canonical" way to determine whether a profile is a testing profile
    # is by checking that it starts with 'test'. This is unbelievably shit and should be fixed a.s.a.p.
    if profile_config.profile_name.startswith('test'):
        testing_mode = True

    message_exchange = get_message_exchange_name(prefix)
    task_exchange = get_task_exchange_name(prefix)
    task_queue = get_launch_queue_name(prefix)

    return kiwipy.rmq.RmqThreadCommunicator.connect(
        connection_params={'url': get_rmq_url()},
        message_exchange=message_exchange,
        encoder=encode_response,
        decoder=decode_response,
        task_exchange=task_exchange,
        task_queue=task_queue,
        task_prefetch_count=task_prefetch_count,
        testing_mode=testing_mode,
    )
