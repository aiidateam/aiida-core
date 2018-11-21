# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""ORM conversion functions, to be used internally by the code"""

from __future__ import absolute_import


def aiida_from_backend_entity(backend_entity):
    """Convert from a backend entity type to an AiiDA frontend entity"""
    from aiida.orm import Node
    from aiida.orm.groups import Group
    from aiida.orm.log import Log
    from aiida.orm.computers import Computer
    from aiida.orm.users import User
    from aiida.orm.authinfos import AuthInfo
    from aiida.orm import implementation

    if isinstance(backend_entity, implementation.BackendComputer):
        return Computer.from_backend_entity(backend_entity)
    if isinstance(backend_entity, implementation.BackendUser):
        return User.from_backend_entity(backend_entity)
    if isinstance(backend_entity, implementation.BackendAuthInfo):
        return AuthInfo.from_backend_entity(backend_entity)
    if isinstance(backend_entity, implementation.BackendGroup):
        return Group.from_backend_entity(backend_entity)
    if isinstance(backend_entity, Node):
        return backend_entity
    if isinstance(backend_entity, Log):
        return backend_entity

    raise ValueError("Unknown entity type '{}'".format(type(backend_entity)))
