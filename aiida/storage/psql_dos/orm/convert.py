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
Module to get the backend instance from the Models instance
"""
from functools import singledispatch

from aiida.storage.psql_dos.models.authinfo import DbAuthInfo
from aiida.storage.psql_dos.models.comment import DbComment
from aiida.storage.psql_dos.models.computer import DbComputer
from aiida.storage.psql_dos.models.group import DbGroup
from aiida.storage.psql_dos.models.log import DbLog
from aiida.storage.psql_dos.models.node import DbLink, DbNode
from aiida.storage.psql_dos.models.user import DbUser

# pylint: disable=cyclic-import


#####################################################################
# Singledispatch to get the backend instance from the Models instance
#####################################################################
@singledispatch
def get_backend_entity(dbmodel, backend):  # pylint: disable=unused-argument
    """
    Default get_backend_entity
    """
    raise TypeError(f"No corresponding AiiDA backend class exists for the model class '{dbmodel.__class__.__name__}'")


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


@get_backend_entity.register(DbLink)
def _(dbmodel, backend):
    """
    Convert a dblink to the backend entity
    """
    from aiida.orm.utils.links import LinkQuadruple
    return LinkQuadruple(dbmodel.input_id, dbmodel.output_id, dbmodel.type, dbmodel.label)
