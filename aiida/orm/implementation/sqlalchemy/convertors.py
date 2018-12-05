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

from __future__ import absolute_import
import singledispatch

from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo as SqlaSchemaDbAuthInfo
from aiida.backends.sqlalchemy.models.computer import DbComputer as SqlaSchemaDbComputer
from aiida.backends.sqlalchemy.models.group import DbGroup as SqlaSchemaDbGroup
from aiida.backends.sqlalchemy.models.node import DbNode as SqlaSchemaDbNode
from aiida.backends.sqlalchemy.models.user import DbUser as SqlaSchemaDbUser

from aiida.common.exceptions import DbContentError
from aiida.plugins.loader import get_plugin_type_from_type_string, load_plugin

from . import authinfo
from . import computer
from . import groups
from . import users

__all__ = ('get_backend_entity',)


#####################################################################
# Singledispatch to get the backend instance from the Models instance
#####################################################################
@singledispatch.singledispatch
def get_backend_entity(dbmodel_instance, _):
    """
    Default get_backend_entity
    """
    raise TypeError("No corresponding AiiDA backend class exists for the DbModel instance {}"
                    .format(dbmodel_instance.__class__.__name__))


################################
# Singledispatch for SQLA Models
################################
@get_backend_entity.register(SqlaSchemaDbUser)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for SQLA DbUser
    """
    return users.SqlaUser.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(SqlaSchemaDbGroup)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for SQLA DbGroup
    """
    return groups.SqlaGroup.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(SqlaSchemaDbComputer)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for SQLA DbGroup
    """
    return computer.SqlaComputer.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(SqlaSchemaDbNode)
def _(dbmodel_instance, _):
    """
    get_backend_entity for SQLA DbNode. It will return an ORM instance since
    there is not Node backend entity yet.
    """
    try:
        plugin_type = get_plugin_type_from_type_string(dbmodel_instance.type)
    except DbContentError:
        raise DbContentError("The type name of node with pk= {} is "
                             "not valid: '{}'".format(dbmodel_instance.pk, dbmodel_instance.type))

    plugin_class = load_plugin(plugin_type, safe=True)
    return plugin_class(dbnode=dbmodel_instance)


@get_backend_entity.register(SqlaSchemaDbAuthInfo)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for SQLA DbAuthInfo
    """
    return authinfo.SqlaAuthInfo.from_dbmodel(dbmodel_instance, backend_instance)
