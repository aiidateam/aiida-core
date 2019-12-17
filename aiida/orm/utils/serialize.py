# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Serialisation functions for AiiDA types

WARNING: Changing the representation of things here may break people's current saved e.g. things like
checkpoints and messages in the RabbitMQ queue so do so with caution.  It is fine to add representers
for new types though.
"""
from functools import partial
import yaml

from plumpy import Bundle
from plumpy.utils import AttributesFrozendict

from aiida import orm
from aiida.common import AttributeDict

_NODE_TAG = '!aiida_node'
_GROUP_TAG = '!aiida_group'
_COMPUTER_TAG = '!aiida_computer'
_ATTRIBUTE_DICT_TAG = '!aiida_attributedict'
_PLUMPY_ATTRIBUTES_FROZENDICT_TAG = '!plumpy:attributes_frozendict'
_PLUMPY_BUNDLE = '!plumpy:bundle'


def represent_node(dumper, node):
    """Represent a node in yaml.

    :param dumper: the dumper to use
    :param node: the node to represent
    :type node: :class:`aiida.orm.nodes.node.Node`
    :return: the representation
    """
    if not node.is_stored:
        raise ValueError('node {}<{}> cannot be represented because it is not stored'.format(type(node), node.uuid))
    return dumper.represent_scalar(_NODE_TAG, '%s' % node.uuid)


def node_constructor(loader, node):
    """Load a node from the yaml representation.

    :param loader: the yaml loader
    :param node: the yaml representation
    :return: the aiida node
    :rtype: :class:`aiida.orm.nodes.node.Node`
    """
    yaml_node = loader.construct_scalar(node)
    return orm.load_node(uuid=yaml_node)


def represent_group(dumper, group):
    """Represent a group in yaml.

    :param dumper: the dumper to use
    :param group: the group to represent
    :type group: :class:`aiida.orm.Group`
    :return: the representation
    """
    if not group.is_stored:
        raise ValueError('group {} cannot be represented because it is not stored'.format(group))
    return dumper.represent_scalar(_GROUP_TAG, '%s' % group.uuid)


def group_constructor(loader, group):
    """Load a group from the yaml representation.

    :param loader: the yaml loader
    :param group: the yaml representation
    :return: the aiida group
    :rtype: :class:`aiida.orm.Group`
    """
    yaml_node = loader.construct_scalar(group)
    return orm.load_group(uuid=yaml_node)


def represent_computer(dumper, computer):
    """Represent a computer in yaml.

    :param dumper: the dumper to use
    :param computer: the computer to represent
    :type computer: :class:`aiida.orm.Computer`
    :return: the representation
    """
    if not computer.is_stored:
        raise ValueError('computer {} cannot be represented because it is not stored'.format(computer))
    return dumper.represent_scalar(_COMPUTER_TAG, '%s' % computer.uuid)


def computer_constructor(loader, computer):
    """Load a computer from the yaml representation.

    :param loader: the yaml loader
    :param computer: the yaml representation
    :return: the aiida computer
    :rtype: :class:`aiida.orm.Computer`
    """
    yaml_node = loader.construct_scalar(computer)
    return orm.Computer.get(uuid=yaml_node)


def represent_mapping(tag, dumper, mapping):
    """Represent a mapping in yaml.

    :param tag: the yaml tag to use
    :param dumper: the dumper to use
    :type dumper: :class:`yaml.dumper.Dumper`
    :param mapping: the mapping to represent
    :return: the representation
    """
    return dumper.represent_mapping(tag, mapping)


def mapping_constructor(mapping_type, loader, mapping):
    """Construct a mapping from the representation.

    :param mapping_type: the class of the mapping to construct, must accept a dictionary as a sole constructor argument
        to be compatible.
    :param loader: the yaml loader
    :type loader: :class:`yaml.loader.Loader`
    :param mapping: the mapping representation
    :return: the reconstructed mapping
    """
    yaml_node = loader.construct_mapping(mapping, deep=True)
    return mapping_type(yaml_node)


def represent_bundle(dumper, bundle):
    """Represent an `plumpy.Bundle` in yaml

    :param tag: the yaml  tag to use
    :param dumper: the dumper to use
    :type dumper: :class:`yaml.dumper.Dumper`
    :param bundle: the bundle to represent
    :return: the representation
    """
    as_dict = dict(bundle)
    return dumper.represent_mapping(_PLUMPY_BUNDLE, as_dict)


def bundle_constructor(loader, bundle):
    """Construct an `plumpy.Bundle` from the representation

    :param loader: the yaml loader
    :type loader: :class:`yaml.loader.Loader`
    :param bundle: the bundle representation
    :return: the mapping type
    """
    yaml_node = loader.construct_mapping(bundle)
    bundle = Bundle.__new__(Bundle)
    bundle.update(yaml_node)
    return bundle


class AiiDADumper(yaml.Dumper):
    """Custom AiiDA yaml dumper.

    Needed so that we don't have to encode each type in the AiiDA graph hierarchy separately using a custom representer.
    """

    def represent_data(self, data):
        if isinstance(data, orm.Node):
            return represent_node(self, data)
        if isinstance(data, orm.Computer):
            return represent_computer(self, data)
        if isinstance(data, orm.Group):
            return represent_group(self, data)

        return super().represent_data(data)


class AiiDALoader(yaml.FullLoader):
    """AiiDA specific yaml loader

    .. note:: we subclass the `FullLoader` which is the one that since `pyyaml>=5.1` is the loader that prevents
        arbitrary code execution. Even though this is in principle only used internally, one could imagine someone
        sharing a database with a maliciously crafted process instance dump, which when reloaded could execute arbitrary
        code. This load prevents this: https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
    """


yaml.add_representer(Bundle, represent_bundle, Dumper=AiiDADumper)
yaml.add_representer(AttributeDict, partial(represent_mapping, _ATTRIBUTE_DICT_TAG), Dumper=AiiDADumper)
yaml.add_constructor(_ATTRIBUTE_DICT_TAG, partial(mapping_constructor, AttributeDict), Loader=AiiDALoader)
yaml.add_representer(
    AttributesFrozendict, partial(represent_mapping, _PLUMPY_ATTRIBUTES_FROZENDICT_TAG), Dumper=AiiDADumper
)
yaml.add_constructor(
    _PLUMPY_ATTRIBUTES_FROZENDICT_TAG, partial(mapping_constructor, AttributesFrozendict), Loader=AiiDALoader
)
yaml.add_constructor(_PLUMPY_BUNDLE, bundle_constructor, Loader=AiiDALoader)
yaml.add_constructor(_NODE_TAG, node_constructor, Loader=AiiDALoader)
yaml.add_constructor(_GROUP_TAG, group_constructor, Loader=AiiDALoader)
yaml.add_constructor(_COMPUTER_TAG, computer_constructor, Loader=AiiDALoader)


def serialize(data, encoding=None):
    """Serialize the given data structure into a yaml dump.

    The function supports standard data containers such as maps and lists as well as AiiDA nodes which will be
    serialized into strings, before the whole data structure is dumped into a string using yaml.

    :param data: the general data to serialize
    :param encoding: optional encoding for the serialized string
    :return: string representation of the serialized data structure or byte array if specific encoding is specified
    """
    if encoding is not None:
        serialized = yaml.dump(data, encoding=encoding, Dumper=AiiDADumper)
    else:
        serialized = yaml.dump(data, Dumper=AiiDADumper)

    return serialized


def deserialize(serialized):
    """Deserialize a yaml dump that represents a serialized data structure.

    .. note:: no need to use `yaml.safe_load` here because the `Loader` will ensure that loading is safe.

    :param serialized: a yaml serialized string representation
    :return: the deserialized data structure
    """
    return yaml.load(serialized, Loader=AiiDALoader)
