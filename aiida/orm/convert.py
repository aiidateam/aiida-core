# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import
"""Module for converting backend entities into frontend, ORM, entities"""
from collections.abc import Iterator, Mapping, Sized
from functools import singledispatch

from aiida.orm.implementation import (
    BackendAuthInfo,
    BackendComment,
    BackendComputer,
    BackendGroup,
    BackendLog,
    BackendNode,
    BackendUser,
)


@singledispatch
def get_orm_entity(backend_entity):
    raise TypeError(f'No corresponding AiiDA ORM class exists for backend instance {backend_entity.__class__.__name__}')


@get_orm_entity.register(Mapping)
def _(backend_entity):
    """Convert all values of the given mapping to ORM entities if they are backend ORM instances."""
    converted = {}

    # Note that we cannot use a simple comprehension because raised `TypeError` should be caught here otherwise only
    # parts of the mapping will be converted.
    for key, value in backend_entity.items():
        try:
            converted[key] = get_orm_entity(value)
        except TypeError:
            converted[key] = value

    return converted


@get_orm_entity.register(list)
@get_orm_entity.register(tuple)
def _(backend_entity):
    """Convert all values of the given list or tuple to ORM entities if they are backend ORM instances.

    Note that we do not register on `collections.abc.Sequence` because that will also match strings.
    """
    if hasattr(backend_entity, '_asdict'):
        # it is a NamedTuple, so return as is
        return backend_entity

    converted = []

    # Note that we cannot use a simple comprehension because raised `TypeError` should be caught here otherwise only
    # parts of the mapping will be converted.
    for value in backend_entity:
        try:
            converted.append(get_orm_entity(value))
        except TypeError:
            converted.append(value)

    return converted


@get_orm_entity.register(BackendGroup)
def _(backend_entity):
    from .groups import load_group_class
    group_class = load_group_class(backend_entity.type_string)
    return group_class.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendComputer)
def _(backend_entity):
    from . import computers
    return computers.Computer.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendUser)
def _(backend_entity):
    from . import users
    return users.User.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendAuthInfo)
def _(backend_entity):
    from . import authinfos
    return authinfos.AuthInfo.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendLog)
def _(backend_entity):
    from . import logs
    return logs.Log.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendComment)
def _(backend_entity):
    from . import comments
    return comments.Comment.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendNode)
def _(backend_entity):
    from .utils.node import load_node_class  # pylint: disable=import-error,no-name-in-module
    node_class = load_node_class(backend_entity.node_type)
    return node_class.from_backend_entity(backend_entity)


class ConvertIterator(Iterator, Sized):
    """
    Iterator that converts backend entities into frontend ORM entities as needed

    See :func:`aiida.orm.Group.nodes` for an example.
    """

    def __init__(self, backend_iterator):
        super().__init__()
        self._backend_iterator = backend_iterator
        self.generator = self._genfunction()

    def _genfunction(self):
        for backend_node in self._backend_iterator:
            yield get_orm_entity(backend_node)

    def __iter__(self):
        return self

    def __len__(self):
        return len(self._backend_iterator)

    def __getitem__(self, value):
        if isinstance(value, slice):
            return [get_orm_entity(backend_node) for backend_node in self._backend_iterator[value]]

        return get_orm_entity(self._backend_iterator[value])

    def __next__(self):
        return next(self.generator)
