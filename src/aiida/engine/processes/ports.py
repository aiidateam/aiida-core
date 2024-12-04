###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA specific implementation of plumpy Ports and PortNamespaces for the ProcessSpec."""

from __future__ import annotations

import re
import warnings
from collections.abc import Mapping
from typing import Any, Callable, Dict, Optional, Sequence

from plumpy import ports
from plumpy.ports import breadcrumbs_to_port

from aiida.common.links import validate_link_label
from aiida.orm import Data, Node, to_aiida_type

__all__ = (
    'PORT_NAMESPACE_SEPARATOR',
    'CalcJobOutputPort',
    'InputPort',
    'OutputPort',
    'PortNamespace',
    'WithNonDb',
    'WithSerialize',
)

PORT_NAME_MAX_CONSECUTIVE_UNDERSCORES = 1
PORT_NAMESPACE_SEPARATOR = '__'  # The character sequence to represent a nested port namespace in a flat link label
OutputPort = ports.OutputPort


class WithNonDb:
    """A mixin that adds support to a port to flag it should not be stored in the database using the ``non_db`` flag."""

    def __init__(self, *args, **kwargs) -> None:
        self._non_db_explicitly_set: bool = bool('non_db' in kwargs)
        non_db = kwargs.pop('non_db', False)
        super().__init__(*args, **kwargs)
        self._non_db: bool = non_db

    @property
    def non_db_explicitly_set(self) -> bool:
        """Return whether the ``non_db`` keyword was explicitly passed in the construction of the ``InputPort``.

        :return: ``True`` if ``non_db`` was explicitly defined during construction, ``False`` otherwise
        """
        return self._non_db_explicitly_set

    @property
    def non_db(self) -> bool:
        """Return whether the value of this ``InputPort`` should be stored in the database.

        :return: ``True`` if it should be stored, ``False`` otherwise
        """
        return self._non_db

    @non_db.setter
    def non_db(self, non_db: bool) -> None:
        """Set whether the value of this ``InputPort`` should be stored as a ``Data`` in the database."""
        self._non_db_explicitly_set = True
        self._non_db = non_db


class WithMetadata:
    """A mixin that allows an input port to be marked as metadata through the keyword ``is_metadata``.

    A metadata input differs from a normal input as in that it is not linked to the ``ProcessNode`` as a ``Data`` node
    but rather is stored on the ``ProcessNode`` itself (as an attribute, for example).
    """

    def __init__(self, *args, **kwargs) -> None:
        self._explicitly_set: bool = bool('is_metadata' in kwargs)
        is_metadata = kwargs.pop('is_metadata', False)
        super().__init__(*args, **kwargs)
        self._is_metadata: bool = is_metadata

    @property
    def is_metadata_explicitly_set(self) -> bool:
        """Return whether the ``is_metadata`` keyword was explicitly passed in the construction of the ``InputPort``.

        :return: ``True`` if ``is_metadata`` was explicitly defined during construction, ``False`` otherwise
        """
        return self._explicitly_set

    @property
    def is_metadata(self) -> bool:
        """Return whether the value of this ``InputPort`` should be stored as a ``Node`` in the database.

        :return: ``True`` if it should be storable as a ``Node``, ``False`` otherwise
        """
        return self._is_metadata

    @is_metadata.setter
    def is_metadata(self, is_metadata: bool) -> None:
        """Set whether the value of this ``InputPort`` should be stored as a ``Node`` in the database.

        :param is_metadata: ``False`` if the port value should be linked as a ``Node``, ``True`` otherwise.
        """
        self._explicitly_set = True
        self._is_metadata = is_metadata


class WithSerialize:
    """A mixin that adds support for a serialization function which is automatically applied on inputs
    that are not AiiDA data types.
    """

    def __init__(self, *args, **kwargs) -> None:
        serializer = kwargs.pop('serializer', None)
        super().__init__(*args, **kwargs)
        self._serializer: Callable[[Any], 'Data'] = serializer

    @property
    def serializer(self) -> Callable[[Any], 'Data'] | None:
        """Return the serializer."""
        return self._serializer

    def serialize(self, value: Any) -> 'Data':
        """Serialize the given value, unless it is ``None``, already a Data type, or no serializer function is defined.

        :param value: the value to be serialized
        :returns: a serialized version of the value or the unchanged value
        """
        if self._serializer is None or value is None or isinstance(value, Data):
            return value

        return self._serializer(value)


class InputPort(WithMetadata, WithSerialize, WithNonDb, ports.InputPort):
    """Sub class of plumpy.InputPort which mixes in the WithSerialize and WithNonDb mixins to support automatic
    value serialization to database storable types and support non database storable input types as well.

    The mixins have to go before the main port class in the superclass order to make sure they have the chance to
    process their specific keywords.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Override the constructor to check the type of the default if set and warn if not immutable."""
        if 'default' in kwargs:
            default = kwargs['default']
            # If the default is specified and it is a node instance, raise a warning. This is to try and prevent that
            # people set node instances as defaults which can cause various problems.
            if default is not ports.UNSPECIFIED and isinstance(default, Node):
                message = (
                    'default of input port `{}` is a `Node` instance, which can lead to unexpected side effects.'
                    ' It is advised to use a lambda instead, e.g.: `default=lambda: orm.Int(5)`.'.format(args[0])
                )
                warnings.warn(UserWarning(message))

        # If the port is not required and defines ``valid_type``, automatically add ``None`` as a valid type
        valid_type = kwargs.get('valid_type', ())

        if not isinstance(valid_type, (tuple, list)):
            valid_type = [valid_type]

        if not kwargs.get('required', True) and valid_type:
            kwargs['valid_type'] = tuple(valid_type) + (type(None),)

        super().__init__(*args, **kwargs)

    def get_description(self) -> Dict[str, str]:
        """Return a description of the InputPort, which will be a dictionary of its attributes

        :returns: a dictionary of the stringified InputPort attributes
        """
        description = super().get_description()
        description['is_metadata'] = f'{self.is_metadata}'
        description['non_db'] = f'{self.non_db}'

        return description


class CalcJobOutputPort(ports.OutputPort):
    """Sub class of plumpy.OutputPort which adds the `_pass_to_parser` attribute."""

    def __init__(self, *args, **kwargs) -> None:
        pass_to_parser = kwargs.pop('pass_to_parser', False)
        super().__init__(*args, **kwargs)
        self._pass_to_parser: bool = pass_to_parser

    @property
    def pass_to_parser(self) -> bool:
        return self._pass_to_parser


class PortNamespace(WithMetadata, WithNonDb, ports.PortNamespace):
    """Sub class of plumpy.PortNamespace which implements the serialize method to support automatic recursive
    serialization of a given mapping onto the ports of the PortNamespace.
    """

    def __setitem__(self, key: str, port: ports.Port) -> None:
        """Ensure that a `Port` being added inherits the `non_db` attribute if not explicitly defined at construction.

        The reasoning is that if a `PortNamespace` has `non_db=True`, which is different from the default value, very
        often all leaves should be also `non_db=True`. To prevent a user from having to specify it manually everytime
        we overload the value here, unless it was specifically set during construction.

        Note that the `non_db` attribute is not present for all `Port` sub classes so we have to check for it first.
        """
        if not isinstance(port, ports.Port):
            raise TypeError('port needs to be an instance of Port')

        self.validate_port_name(key)

        if hasattr(port, 'is_metadata_explicitly_set') and not port.is_metadata_explicitly_set:  # type: ignore[attr-defined]
            port.is_metadata = self.is_metadata  # type: ignore[attr-defined]

        if hasattr(port, 'non_db_explicitly_set') and not port.non_db_explicitly_set:  # type: ignore[attr-defined]
            port.non_db = self.non_db  # type: ignore[attr-defined]

        # If the port is not metadata (signified by ``is_metadata`` and ``non_db`` being ``False`` if defined) and it
        # does not already define a serializer, set the default serializer to ``to_aiida_type``.
        if (
            ((hasattr(port, 'is_metadata') and not port.is_metadata) and (hasattr(port, 'non_db') and not port.non_db))
            and hasattr(port, 'serializer')
            and port.serializer is None
        ):
            port._serializer = to_aiida_type

        super().__setitem__(key, port)

    @staticmethod
    def validate_port_name(port_name: str) -> None:
        """Validate the given port name.

        Valid port names adhere to the following restrictions:

            * Is a valid link label (see below)
            * Does not contain two or more consecutive underscores

        Valid link labels adhere to the following restrictions:

            * Has to be a valid python identifier
            * Can only contain alphanumeric characters and underscores
            * Can not start or end with an underscore

        :param port_name: the proposed name of the port to be added
        :raise TypeError: if the port name is not a string type
        :raise ValueError: if the port name is invalid
        """
        try:
            validate_link_label(port_name)
        except ValueError as exception:
            raise ValueError(f'invalid port name `{port_name}`: {exception}')

        # Following regexes will match all groups of consecutive underscores where each group will be of the form
        # `('___', '_')`, where the first element is the matched group of consecutive underscores.
        consecutive_underscores = [match[0] for match in re.findall(r'((_)\2+)', port_name)]

        if any(len(entry) > PORT_NAME_MAX_CONSECUTIVE_UNDERSCORES for entry in consecutive_underscores):
            raise ValueError(f'invalid port name `{port_name}`: more than two consecutive underscores')

    def serialize(self, mapping: Optional[Dict[str, Any]], breadcrumbs: Sequence[str] = ()) -> Optional[Dict[str, Any]]:
        """Serialize the given mapping onto this `Portnamespace`.

        It will recursively call this function on any nested `PortNamespace` or the serialize function on any `Ports`.

        :param mapping: a mapping of values to be serialized
        :param breadcrumbs: a tuple with the namespaces of parent namespaces
        :returns: the serialized mapping
        """
        if mapping is None:
            return None

        breadcrumbs = (*breadcrumbs, self.name)

        if not isinstance(mapping, Mapping):
            port_name = breadcrumbs_to_port(breadcrumbs)
            raise TypeError(f'port namespace `{port_name}` received `{type(mapping)}` instead of a dictionary')

        result = {}

        for name, value in mapping.items():
            if name in self:
                port = self[name]
                if isinstance(port, PortNamespace):
                    result[name] = port.serialize(value, breadcrumbs)
                elif isinstance(port, InputPort):
                    result[name] = port.serialize(value)
                else:
                    raise AssertionError(f'port does not have a serialize method: {port}')
            else:
                result[name] = value

        return result
