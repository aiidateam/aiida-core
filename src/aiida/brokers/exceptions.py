###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from kiwipy.                          #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The kiwipy license is reproduced in open_source_licenses.txt.          #
###########################################################################
"""Exceptions raised by the broker communication layer."""

import concurrent.futures

__all__ = (
    'CommunicatorClosed',
    'DeliveryFailed',
    'DuplicateSubscriberIdentifier',
    'QueueEmpty',
    'RemoteException',
    'TaskRejected',
    'TimeoutError',
    'UnroutableError',
)


class RemoteException(Exception):  # noqa: N818
    """An exception occurred at the remote end of the call."""


class DeliveryFailed(Exception):  # noqa: N818
    """Failed to deliver a message."""


class UnroutableError(DeliveryFailed):
    """The message was unroutable."""


class TaskRejected(Exception):  # noqa: N818
    """A task was rejected at the remote end."""


class QueueEmpty(Exception):  # noqa: N818
    """Could not get the next message from the queue because it is empty."""


class DuplicateSubscriberIdentifier(Exception):  # noqa: N818
    """Failed to add a subscriber because the identifier supplied is already in use."""


class CommunicatorClosed(Exception):  # noqa: N818
    """Raised when an operation is attempted on a closed communicator."""


TimeoutError = concurrent.futures.TimeoutError
