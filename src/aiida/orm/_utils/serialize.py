###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Serialisation functions for AiiDA types

WARNING: Changing the representation of things here may break people's current saved e.g. things like
checkpoints and messages in the RabbitMQ queue so do so with caution.  It is fine to add representers
for new types though.
"""

from __future__ import annotations

import inspect
from dataclasses import asdict, is_dataclass
from enum import Enum
from functools import partial
from typing import Any, Protocol, Type, overload

import yaml
from plumpy import Bundle, get_object_loader
from plumpy.utils import AttributesFrozendict

from aiida import orm
from aiida.common import AttributeDict
from aiida.orm.utils.managers import NodeLinksManager

_ENUM_TAG = '!enum'
_DATACLASS_TAG = '!dataclass'
_NODE_TAG = '!aiida_node'
_NODE_LINKS_MANAGER_TAG = '!aiida_node_links_manager'
_GROUP_TAG = '!aiida_group'
_COMPUTER_TAG = '!aiida_computer'
_ATTRIBUTE_DICT_TAG = '!aiida_attributedict'
_PLUMPY_ATTRIBUTES_FROZENDICT_TAG = '!plumpy:attributes_frozendict'
_PLUMPY_BUNDLE = '!plumpy:bundle'


def represent_enum(dumper: yaml.Dumper, enum: Enum) -> yaml.ScalarNode:
    """Represent an arbitrary enum in yaml."""
    loader = get_object_loader()
    return dumper.represent_scalar(_ENUM_TAG, f'{loader.identify_object(enum)}|{enum.value}')


def enum_constructor(loader: yaml.Loader, serialized: yaml.Node) -> Enum:
    """Construct an enum from the serialized representation."""
    deserialized: str = loader.construct_scalar(serialized)  # type: ignore[arg-type]
    identifier, value = deserialized.split('|')
    cls = get_object_loader().load_object(identifier)
    enum = cls(value)
    return enum


def represent_dataclass(dumper: yaml.Dumper, obj: Any) -> yaml.MappingNode:
    """Represent an arbitrary dataclass in yaml."""
    loader = get_object_loader()
    data = {
        '__type__': loader.identify_object(obj.__class__),
        '__fields__': asdict(obj),
    }
    return dumper.represent_mapping(_DATACLASS_TAG, data)


def dataclass_constructor(loader: yaml.Loader, serialized: yaml.Node) -> Any:
    """Construct a dataclass from the serialized representation."""
    deserialized = loader.construct_mapping(serialized, deep=True)  # type: ignore[arg-type]
    identifier = deserialized['__type__']
    cls = get_object_loader().load_object(identifier)
    data = deserialized['__fields__']
    return cls(**data)


def represent_node(dumper: yaml.Dumper, node: orm.Node) -> yaml.ScalarNode:
    """Represent a node in yaml."""
    if not node.is_stored:
        raise ValueError(f'node {type(node)}<{node.uuid}> cannot be represented because it is not stored')
    return dumper.represent_scalar(_NODE_TAG, f'{node.uuid}')


def node_constructor(loader: yaml.Loader, node: yaml.Node) -> orm.Node:
    """Load a node from the yaml representation."""
    yaml_node = loader.construct_scalar(node)  # type: ignore[arg-type]
    return orm.load_node(uuid=yaml_node)


def represent_node_links_manager(dumper: yaml.Dumper, node_links_manager: NodeLinksManager) -> yaml.MappingNode:
    """Represent a link in yaml."""
    data = {
        'incoming': node_links_manager._incoming,
        'link_type': node_links_manager._link_type.value,
        'node': node_links_manager._node.uuid,
    }
    return dumper.represent_mapping(_NODE_LINKS_MANAGER_TAG, data)


def node_links_manager_constructor(loader: yaml.Loader, node_links_manager: yaml.Node) -> NodeLinksManager:
    """Load a link from the yaml representation."""
    from aiida.common.links import LinkType

    yaml_node_links_manager = loader.construct_mapping(node_links_manager)  # type: ignore[arg-type]
    link_type = LinkType(yaml_node_links_manager['link_type'])
    node = orm.load_node(uuid=yaml_node_links_manager['node'])
    incoming = yaml_node_links_manager['incoming']
    return NodeLinksManager(node=node, link_type=link_type, incoming=incoming)


def represent_group(dumper: yaml.Dumper, group: orm.Group) -> yaml.ScalarNode:
    """Represent a group in yaml."""
    if not group.is_stored:
        raise ValueError(f'group {group} cannot be represented because it is not stored')
    return dumper.represent_scalar(_GROUP_TAG, f'{group.uuid}')


def group_constructor(loader: yaml.Loader, group: yaml.Node) -> orm.Group:
    """Load a group from the yaml representation."""
    yaml_node = loader.construct_scalar(group)  # type: ignore[arg-type]
    return orm.load_group(uuid=yaml_node)


def represent_computer(dumper: yaml.Dumper, computer: orm.Computer) -> yaml.ScalarNode:
    """Represent a computer in yaml."""
    if not computer.is_stored:
        raise ValueError(f'computer {computer} cannot be represented because it is not stored')
    return dumper.represent_scalar(_COMPUTER_TAG, f'{computer.uuid}')


def computer_constructor(loader: yaml.Loader, computer: yaml.Node) -> orm.Computer:
    """Load a computer from the yaml representation."""
    yaml_node = loader.construct_scalar(computer)  # type: ignore[arg-type]
    return orm.Computer.collection.get(uuid=yaml_node)


def represent_mapping(tag: str, dumper: yaml.Dumper, mapping: Any) -> yaml.MappingNode:
    """Represent a mapping in yaml."""
    return dumper.represent_mapping(tag, mapping)


class _MappingType(Protocol):
    def __init__(self, mapping: dict) -> None: ...


def mapping_constructor(
    mapping_type: Type[_MappingType], loader: yaml.Loader, mapping: yaml.MappingNode
) -> _MappingType:
    """Construct a mapping from the representation."""
    yaml_node = loader.construct_mapping(mapping, deep=True)
    return mapping_type(yaml_node)


def represent_bundle(dumper: yaml.Dumper, bundle: Bundle) -> yaml.MappingNode:
    """Represent an `plumpy.Bundle` in yaml."""
    as_dict = dict(bundle)
    return dumper.represent_mapping(_PLUMPY_BUNDLE, as_dict)


def bundle_constructor(loader: yaml.Loader, bundle: yaml.Node) -> Bundle:
    """Construct an `plumpy.Bundle` from the representation."""
    yaml_node = loader.construct_mapping(bundle)  # type: ignore[arg-type]
    bundle_inst = Bundle.__new__(Bundle)
    bundle_inst.update(yaml_node)
    return bundle_inst


class AiiDADumper(yaml.Dumper):
    """Custom AiiDA yaml dumper.

    Needed so that we don't have to encode each type in the AiiDA graph hierarchy separately using a custom representer.
    """

    def represent_data(self, data):
        if isinstance(data, orm.Node):
            return represent_node(self, data)
        if isinstance(data, NodeLinksManager):
            return represent_node_links_manager(self, data)
        if isinstance(data, orm.Computer):
            return represent_computer(self, data)
        if isinstance(data, orm.Group):
            return represent_group(self, data)
        if is_dataclass(data) and not inspect.isclass(data):
            return represent_dataclass(self, data)

        return super().represent_data(data)


class AiiDALoader(yaml.Loader):
    """AiiDA specific yaml loader

    .. note:: The `AiiDALoader` should only be used on trusted input, since it uses the `yaml.Loader` which is not safe.
        When importing a shared database, we strip all process node checkpoints to avoid this being a security risk.
    """


yaml.add_representer(Enum, represent_enum, Dumper=AiiDADumper)
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
yaml.add_constructor(_NODE_LINKS_MANAGER_TAG, node_links_manager_constructor, Loader=AiiDALoader)
yaml.add_constructor(_GROUP_TAG, group_constructor, Loader=AiiDALoader)
yaml.add_constructor(_COMPUTER_TAG, computer_constructor, Loader=AiiDALoader)
yaml.add_constructor(_ENUM_TAG, enum_constructor, Loader=AiiDALoader)
yaml.add_constructor(_DATACLASS_TAG, dataclass_constructor, Loader=AiiDALoader)


@overload
def serialize(data: Any, encoding: None = None) -> str: ...


@overload
def serialize(data: Any, encoding: str) -> bytes: ...


def serialize(data: Any, encoding: str | None = None) -> str | bytes:
    """Serialize the given data structure into a yaml dump.

    The function supports standard data containers such as maps and lists as well as AiiDA nodes which will be
    serialized into strings, before the whole data structure is dumped into a string using yaml.

    :param data: the general data to serialize
    :param encoding: optional encoding for the serialized string
    :return: string representation of the serialized data structure or byte array if specific encoding is specified
    """
    serialized: bytes | str

    if encoding is not None:
        serialized = yaml.dump(data, encoding=encoding, Dumper=AiiDADumper)
    else:
        serialized = yaml.dump(data, Dumper=AiiDADumper)

    return serialized


def deserialize_unsafe(serialized: str) -> Any:
    """Deserialize a yaml dump that represents a serialized data structure.

    .. note:: This function should not be used on untrusted input, since it is built upon `yaml.Loader` which is unsafe.

    :param serialized: a yaml serialized string representation
    :return: the deserialized data structure
    """
    return yaml.load(serialized, Loader=AiiDALoader)
