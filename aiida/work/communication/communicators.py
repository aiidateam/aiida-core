# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Methods for creating, setting and getting the global RabbitMQ communicator."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import functools

from kiwipy.rmq import RmqThreadCommunicator

from aiida.work import rmq
from aiida.utils import serialize

__all__ = ['create_communicator', 'get_communicator', 'set_communicator']

COMMUNICATOR = None


def create_communicator(url=None, prefix=None, task_prefetch_count=None):
    """
    Create a Communicator

    :param prefix: optionally a specific prefix to use for the RMQ connection
    :return: the communicator instance
    :rtype: :class:`~kiwipy.rmq.communicator.RmqThreadCommunicator`
    """
    from aiida.common.profile import get_profile

    profile = get_profile()

    if task_prefetch_count is None:
        task_prefetch_count = rmq._RMQ_TASK_PREFETCH_COUNT  # pylint: disable=protected-access

    if url is None:
        url = rmq.get_rmq_url()

    if prefix is None:
        prefix = rmq.get_rmq_prefix()

    # This needs to be here, because the verdi commands will call this function and when called in unit tests the
    # testing_mode cannot be set.
    testing_mode = True if profile.is_test_profile else False

    message_exchange = rmq.get_message_exchange_name(prefix)
    task_exchange = rmq.get_task_exchange_name(prefix)
    task_queue = rmq.get_launch_queue_name(prefix)

    return RmqThreadCommunicator.connect(
        connection_params={'url': url},
        message_exchange=message_exchange,
        encoder=functools.partial(serialize.serialize, encoding='utf-8'),
        decoder=serialize.deserialize,
        task_exchange=task_exchange,
        task_queue=task_queue,
        task_prefetch_count=task_prefetch_count,
        testing_mode=testing_mode,
    )


def get_communicator():
    """
    Get the global communicator instance

    :returns: the global communicator
    """
    global COMMUNICATOR

    if COMMUNICATOR is None:
        COMMUNICATOR = create_communicator()

    return COMMUNICATOR


def set_communicator(communicator):
    """
    Set the global communicator instance

    :param communicator: the communicator instance to set as the global runner
    """
    global COMMUNICATOR
    COMMUNICATOR = communicator
