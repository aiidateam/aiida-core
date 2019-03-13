# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module to get the backend instance from the Models instance
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

try:  # Python3
    from functools import singledispatch
except ImportError:  # Python2
    from singledispatch import singledispatch

from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
from aiida.backends.sqlalchemy.models.comment import DbComment
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.group import DbGroup
from aiida.backends.sqlalchemy.models.log import DbLog
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.backends.sqlalchemy.models.user import DbUser

__all__ = ('get_backend_entity',)

# pylint: disable=cyclic-import


#####################################################################
# Singledispatch to get the backend instance from the Models instance
#####################################################################
@singledispatch
def get_backend_entity(dbmodel, backend):  # pylint: disable=unused-argument
    """
    Default get_backend_entity
    """
    raise TypeError("No corresponding AiiDA backend class exists for the model class '{}'".format(
        dbmodel.__class__.__name__))


################################
# Singledispatch for SQLA Models
################################
@get_backend_entity.register(DbUser)
def _(dbmodel, backend):
    """
    get_backend_entity for SQLA DbUser
    """
    from . import users
    return users.SqlaUser.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(DbGroup)
def _(dbmodel, backend):
    """
    get_backend_entity for SQLA DbGroup
    """
    from . import groups
    return groups.SqlaGroup.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(DbComputer)
def _(dbmodel, backend):
    """
    get_backend_entity for SQLA DbGroup
    """
    from . import computers
    return computers.SqlaComputer.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(DbNode)
def _(dbmodel, backend):
    """
    get_backend_entity for SQLA DbNode. It will return an ORM instance since
    there is not Node backend entity yet.
    """
    from . import nodes
    return nodes.SqlaNode.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(DbAuthInfo)
def _(dbmodel, backend):
    """
    get_backend_entity for SQLA DbAuthInfo
    """
    from . import authinfos
    return authinfos.SqlaAuthInfo.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(DbComment)
def _(dbmodel, backend):
    """
    Get the comment from the model
    """
    from . import comments
    return comments.SqlaComment.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(DbLog)
def _(dbmodel, backend):
    """
    Get the comment from the model
    """
    from . import logs
    return logs.SqlaLog.from_dbmodel(dbmodel, backend)
