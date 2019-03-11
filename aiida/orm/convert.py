# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import,ungrouped-imports
"""Module for converting backend entities into frontend, ORM, entities"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from collections import Mapping

try:  # Python3
    from functools import singledispatch
except ImportError:  # Python2
    from singledispatch import singledispatch

try:
    from collections.abc import Iterator, Sized  # only works on python 3.3+
except ImportError:
    from collections import Iterator, Sized

from aiida.orm.implementation import BackendComputer, BackendGroup, BackendUser, BackendAuthInfo, BackendComment, \
    BackendLog, BackendNode


@singledispatch
def get_orm_entity(backend_entity):
    raise TypeError("No corresponding AiiDA ORM class exists for backend instance {}".format(
        backend_entity.__class__.__name__))


@get_orm_entity.register(Mapping)
def _(backend_entity):
    return {key: get_orm_entity(value) for key, value in backend_entity.items()}


@get_orm_entity.register(BackendGroup)
def _(backend_entity):
    from . import groups
    return groups.Group.from_backend_entity(backend_entity)


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
    from .utils.node import load_node_class
    node_class = load_node_class(backend_entity.node_type)
    return node_class.from_backend_entity(backend_entity)


class ConvertIterator(Iterator, Sized):
    """
    Iterator that converts backend entities into frontend ORM entities as needed

    See :func:`aiida.orm.Group.nodes` for an example.
    """

    def __init__(self, backend_iterator):
        super(ConvertIterator, self).__init__()
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

    # For future python-3 compatibility
    def __next__(self):
        return next(self.generator)

    def next(self):
        return next(self.generator)
