# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all common top level AiiDA entity classes and methods"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import singledispatch

from aiida.orm.implementation.computers import BackendComputer
from aiida.orm.implementation.groups import BackendGroup
from aiida.orm.implementation.users import BackendUser
from aiida.orm.node import Node

from . import groups
from . import computers
from . import users


##################################################################
# Singledispatch to get the ORM instance from the backend instance
##################################################################
@singledispatch.singledispatch
def get_orm_entity(backend_entity):
    raise TypeError("No corresponding AiiDA ORM class exists for backend instance {}"
                    .format(backend_entity.__class__.__name__))


@get_orm_entity.register(BackendGroup)
def _(backend_entity):
    return groups.Group.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendComputer)
def _(backend_entity):
    return computers.Computer.from_backend_entity(backend_entity)


@get_orm_entity.register(BackendUser)
def _(backend_entity):
    return users.User.from_backend_entity(backend_entity)


@get_orm_entity.register(Node)
def _(backend_entity):
    return backend_entity
