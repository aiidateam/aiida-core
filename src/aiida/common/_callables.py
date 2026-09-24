###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Internal callable serialization and source recording."""

from __future__ import annotations

import typing as t


def dumps(value: t.Any) -> bytes:
    """Serialize a callable, including any state it closes over, to bytes.

    `cloudpickle` records writer-importable callables by reference and dynamic definitions by value. Referenced
    modules must also be importable by the reader; serialization does not establish reader-side availability.

    :param value: The callable to serialize.
    :returns: The serialized callable.
    :raises TypeError: If the callable cannot be serialized.
    """
    import cloudpickle

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg: str = f'`{value}` could not be serialized: {exception}'
        raise TypeError(msg) from exception


def loads(payload: bytes) -> t.Any:
    """Deserialize a callable that was serialized with :func:`dumps`.

    :param payload: The serialized callable.
    :returns: The deserialized callable.
    :raises ValueError: If the payload cannot be deserialized.
    """
    import cloudpickle

    try:
        return cloudpickle.loads(payload)
    except Exception as exception:
        msg: str = f'the serialized callable could not be deserialized: {exception}'
        raise ValueError(msg) from exception
