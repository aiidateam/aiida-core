# -*- coding: utf-8 -*-
"""Serialisation functions for AiiDA types"""
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import collections
import uuid
from ast import literal_eval

import six
from plumpy.utils import AttributesFrozendict

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Group, Node, load_group, load_node

_PREFIX_KEY_TUPLE = 'tuple():'
_PREFIX_VALUE_NODE = 'aiida_node:'
_PREFIX_VALUE_GROUP = 'aiida_group:'
_PREFIX_VALUE_UUID = 'aiida_uuid:'


def encode_key(key):
    """
    Helper function for the serialize_data function which may need to serialize a
    dictionary that uses tuples as keys. This function will encode the tuple into
    a string such that it is JSON serializable

    :param key: the key to encode
    :return: the encoded key
    """
    if isinstance(key, tuple):
        return '{}{}'.format(_PREFIX_KEY_TUPLE, key)

    return key


def decode_key(key):
    """
    Helper function for the deserialize_data function which can undo the key encoding
    of tuple keys done by the encode_key function

    :param key: the key to decode
    :return: the decoded key
    """

    if isinstance(key, six.string_types) and key.startswith(_PREFIX_KEY_TUPLE):
        return literal_eval(key[len(_PREFIX_KEY_TUPLE):])

    return key


def serialize_data(data):
    """
    Serialize a value or collection that may potentially contain AiiDA nodes, which
    will be serialized to their UUID. Keys encountered in any mappings, such as a dictionary,
    will also be encoded if necessary. An example is where tuples are used as keys in the
    pseudo potential input dictionaries. These operations will ensure that the returned data is
    JSON serializable.

    :param data: a single value or collection
    :return: the serialized data with the same internal structure
    """
    # pylint: disable=too-many-return-statements

    if isinstance(data, Node):
        return '{}{}'.format(_PREFIX_VALUE_NODE, data.uuid)
    if isinstance(data, Group):
        return '{}{}'.format(_PREFIX_VALUE_GROUP, data.uuid)
    if isinstance(data, uuid.UUID):
        return '{}{}'.format(_PREFIX_VALUE_UUID, data)
    if isinstance(data, AttributeDict):
        return AttributeDict({encode_key(key): serialize_data(value) for key, value in data.items()})
    if isinstance(data, AttributesFrozendict):
        return AttributesFrozendict({encode_key(key): serialize_data(value) for key, value in data.items()})
    if isinstance(data, collections.Mapping):
        return {encode_key(key): serialize_data(value) for key, value in data.items()}
    if isinstance(data, collections.Sequence) and not isinstance(data, six.string_types):
        return [serialize_data(value) for value in data]

    return data


def deserialize_data(data):
    """
    Deserialize a single value or a collection that may contain serialized AiiDA nodes. This is
    essentially the inverse operation of serialize_data which will reload node instances from
    the serialized UUID data. Encoded tuples that are used as dictionary keys will be decoded.

    :param data: serialized data
    :return: the deserialized data with keys decoded and node instances loaded from UUID's
    """
    # pylint: disable=too-many-return-statements

    if isinstance(data, AttributeDict):
        return AttributeDict({decode_key(key): deserialize_data(value) for key, value in data.items()})
    if isinstance(data, AttributesFrozendict):
        return AttributesFrozendict({decode_key(key): deserialize_data(value) for key, value in data.items()})
    if isinstance(data, collections.Mapping):
        return {decode_key(key): deserialize_data(value) for key, value in data.items()}
    if isinstance(data, collections.Sequence) and not isinstance(data, six.string_types):
        return [deserialize_data(value) for value in data]
    if isinstance(data, six.string_types) and data.startswith(_PREFIX_VALUE_NODE):
        return load_node(uuid=data[len(_PREFIX_VALUE_NODE):])
    if isinstance(data, six.string_types) and data.startswith(_PREFIX_VALUE_GROUP):
        return load_group(uuid=data[len(_PREFIX_VALUE_GROUP):])
    if isinstance(data, six.string_types) and data.startswith(_PREFIX_VALUE_UUID):
        return uuid.UUID(data[len(_PREFIX_VALUE_UUID):])

    return data
