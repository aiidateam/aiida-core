# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA specific implementation of plumpy Ports and PortNamespaces for the ProcessSpec."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from collections import Mapping
from plumpy import ports


class WithNonDb(object):  # pylint: disable=useless-object-inheritance
    """
    A mixin that adds support to a port to flag a that should not be stored
    in the database using the non_db=True flag.

    The mixins have to go before the main port class in the superclass order
    to make sure the mixin has the chance to strip out the non_db keyword.
    """

    def __init__(self, *args, **kwargs):
        self._non_db_explicitly_set = bool('non_db' in kwargs)
        non_db = kwargs.pop('non_db', False)
        super(WithNonDb, self).__init__(*args, **kwargs)
        self._non_db = non_db

    @property
    def non_db_explicitly_set(self):
        """Return whether the a value for `non_db` was explicitly passed in the construction of the `Port`.

        :return: boolean, True if `non_db` was explicitly defined during construction, False otherwise
        """
        return self._non_db_explicitly_set

    @property
    def non_db(self):
        """Return whether the value of this `Port` should be stored as a `Node` in the database.

        :return: boolean, True if it should be storable as a `Node`, False otherwise
        """
        return self._non_db

    @non_db.setter
    def non_db(self, non_db):
        """Set whether the value of this `Port` should be stored as a `Node` in the database.

        :param non_db: boolean
        """
        self._non_db_explicitly_set = True
        self._non_db = non_db


class WithSerialize(object):  # pylint: disable=useless-object-inheritance
    """
    A mixin that adds support for a serialization function which is automatically applied on inputs
    that are not AiiDA data types.
    """

    def __init__(self, *args, **kwargs):
        serializer = kwargs.pop('serializer', None)
        super(WithSerialize, self).__init__(*args, **kwargs)
        self._serializer = serializer

    def serialize(self, value):
        """
        Serialize the given value if it is not already a Data type and a serializer function is defined

        :param value: the value to be serialized
        :returns: a serialized version of the value or the unchanged value
        """
        from aiida.orm import Data

        if self._serializer is None or isinstance(value, Data):
            return value

        return self._serializer(value)


class InputPort(WithSerialize, WithNonDb, ports.InputPort):
    """
    Sub class of plumpy.InputPort which mixes in the WithSerialize and WithNonDb mixins to support automatic
    value serialization to database storable types and support non database storable input types as well.
    """

    def get_description(self):
        """
        Return a description of the InputPort, which will be a dictionary of its attributes

        :returns: a dictionary of the stringified InputPort attributes
        """
        description = super(InputPort, self).get_description()
        description['non_db'] = '{}'.format(self.non_db)

        return description


class CalcJobOutputPort(ports.OutputPort):
    """Sub class of plumpy.OutputPort which adds the `_pass_to_parser` attribute."""

    def __init__(self, *args, **kwargs):
        pass_to_parser = kwargs.pop('pass_to_parser', False)
        super(CalcJobOutputPort, self).__init__(*args, **kwargs)
        self._pass_to_parser = pass_to_parser

    @property
    def pass_to_parser(self):
        return self._pass_to_parser


class PortNamespace(WithNonDb, ports.PortNamespace):
    """
    Sub class of plumpy.PortNamespace which implements the serialize method to support automatic recursive
    serialization of a given mapping onto the ports of the PortNamespace.
    """

    def __setitem__(self, key, port):
        """Ensure that a `Port` being added inherits the `non_db` attribute if not explicitly defined at construction.

        The reasoning is that if a `PortNamespace` has `non_db=True`, which is different from the default value, very
        often all leaves should be also `non_db=True`. To prevent a user from having to specify it manually everytime
        we overload the value here, unless it was specifically set during construction.

        Note that the `non_db` attribute is not present for all `Port` sub classes so we have to check for it first.
        """
        if not isinstance(port, ports.Port):
            raise TypeError('port needs to be an instance of Port')

        if hasattr(port, 'non_db_explicitly_set') and not port.non_db_explicitly_set:
            port.non_db = self.non_db

        super(PortNamespace, self).__setitem__(key, port)

    def serialize(self, mapping):
        """
        Serialize the given mapping onto this Portnamespace. It will recursively call this function on any
        nested PortNamespace or the serialize function on any Ports.

        :param mapping: a mapping of values to be serialized
        :returns: the serialized mapping
        """
        from aiida.common.lang import type_check

        if mapping is None:
            return None

        type_check(mapping, Mapping)

        result = {}

        for name, value in mapping.items():
            if name in self:
                port = self[name]
                result[name] = port.serialize(value)
            else:
                result[name] = value

        return result
