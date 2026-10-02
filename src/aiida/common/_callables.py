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
    """Serialize a callable and captured state with `cloudpickle`.

    Referenced modules must be importable when deserializing.

    :raises TypeError: If serialization fails.
    """
    import cloudpickle

    try:
        return t.cast(bytes, cloudpickle.dumps(value))
    except Exception as exception:
        msg: str = f'`{value}` could not be serialized: {exception}'
        raise TypeError(msg) from exception


def loads(payload: bytes) -> t.Any:
    """Deserialize a callable from a trusted :func:`dumps` payload.

    :raises ValueError: If deserialization fails.
    """
    import cloudpickle

    try:
        return cloudpickle.loads(payload)
    except Exception as exception:
        msg: str = f'the serialized callable could not be deserialized: {exception}'
        raise ValueError(msg) from exception
