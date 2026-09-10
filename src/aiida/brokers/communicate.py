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
"""Factory to create a communicator from a URI."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

__all__ = ('DEFAULT_COMM_URI', 'connect')

DEFAULT_COMM_URI = 'amqp://guest:guest@127.0.0.1/'


def connect(uri: str = DEFAULT_COMM_URI, **kwargs: Any) -> Any:
    """Create a communicator connection using a URI."""
    if urlsplit(uri).scheme in ('amqp', 'amqps'):
        from aiida.brokers.rabbitmq import threadcomms  # pylint: disable=import-outside-toplevel

        return threadcomms.connect(connection_params=uri, **kwargs)

    msg = f"Unknown communicator uri '{uri}'"
    raise ValueError(msg)
