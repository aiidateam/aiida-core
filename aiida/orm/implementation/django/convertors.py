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

from aiida.backends.djsite.db.models import DbAuthInfo as DjangoSchemaDbAuthInfo
from aiida.backends.djsite.db.models import DbComputer as DjangoSchemaDbComputer
from aiida.backends.djsite.db.models import DbGroup as DjangoSchemaDbGroup
from aiida.backends.djsite.db.models import DbNode as DjangoSchemaDbNode
from aiida.backends.djsite.db.models import DbUser as DjangoSchemaDbUser

from aiida.orm.implementation.django.dummy_model import DbAuthInfo as DummySchemaDbAuthInfo
from aiida.orm.implementation.django.dummy_model import DbComputer as DummySchemaDbComputer
from aiida.orm.implementation.django.dummy_model import DbGroup as DummySchemaDbGroup
from aiida.orm.implementation.django.dummy_model import DbNode as DummySchemaDbNode
from aiida.orm.implementation.django.dummy_model import DbUser as DummySchemaDbUser

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
    Default get_backend_entity from DbModel
    """
    raise TypeError("No corresponding AiiDA backend class exists for the DbModel instance {}"
                    .format(dbmodel_instance.__class__.__name__))


##################################
# Singledispatch for Django Models
##################################
@get_backend_entity.register(DjangoSchemaDbUser)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbUser
    """
    return users.DjangoUser.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbGroup)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbGroup
    """
    return groups.DjangoGroup.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbComputer)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbGroup
    """
    return computer.DjangoComputer.from_dbmodel(dbmodel_instance, backend_instance)


@get_backend_entity.register(DjangoSchemaDbNode)
def _(dbmodel_instance, _):
    """
    get_backend_entity for Django DbNode. It will return an ORM instance since
    there is not Node backend entity yet.
    """
    try:
        plugin_type = get_plugin_type_from_type_string(dbmodel_instance.type)
    except DbContentError:
        raise DbContentError("The type name of node with pk= {} is "
                             "not valid: '{}'".format(dbmodel_instance.pk, dbmodel_instance.type))

    plugin_class = load_plugin(plugin_type, safe=True)
    return plugin_class(dbnode=dbmodel_instance)


@get_backend_entity.register(DjangoSchemaDbAuthInfo)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for Django DbAuthInfo
    """
    return authinfo.DjangoAuthInfo.from_dbmodel(dbmodel_instance, backend_instance)


########################################
# Singledispatch for Dummy Django Models
########################################
@get_backend_entity.register(DummySchemaDbUser)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for DummyModel DbUser.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    djuser_instance = DjangoSchemaDbUser(
        id=dbmodel_instance.id,
        email=dbmodel_instance.email,
        password=dbmodel_instance.password,
        first_name=dbmodel_instance.first_name,
        last_name=dbmodel_instance.last_name,
        institution=dbmodel_instance.institution,
        is_staff=dbmodel_instance.is_staff,
        is_active=dbmodel_instance.is_active,
        last_login=dbmodel_instance.last_login,
        date_joined=dbmodel_instance.date_joined)
    return users.DjangoUser.from_dbmodel(djuser_instance, backend_instance)


@get_backend_entity.register(DummySchemaDbGroup)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for DummyModel DbGroup.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    djgroup_instance = DjangoSchemaDbGroup(
        id=dbmodel_instance.id,
        type=dbmodel_instance.type,
        uuid=dbmodel_instance.uuid,
        name=dbmodel_instance.name,
        time=dbmodel_instance.time,
        description=dbmodel_instance.description,
        user_id=dbmodel_instance.user_id,
    )
    return groups.DjangoGroup.from_dbmodel(djgroup_instance, backend_instance)


@get_backend_entity.register(DummySchemaDbComputer)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for DummyModel DbComputer.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    djcomputer_instance = DjangoSchemaDbComputer(
        id=dbmodel_instance.id,
        uuid=dbmodel_instance.uuid,
        name=dbmodel_instance.name,
        hostname=dbmodel_instance.hostname,
        description=dbmodel_instance.description,
        enabled=dbmodel_instance.enabled,
        transport_type=dbmodel_instance.transport_type,
        scheduler_type=dbmodel_instance.scheduler_type,
        transport_params=dbmodel_instance.transport_params,
        metadata=dbmodel_instance._metadata)  # pylint: disable=protected-access
    return computer.DjangoComputer.from_dbmodel(djcomputer_instance, backend_instance)


@get_backend_entity.register(DummySchemaDbNode)
def _(dbmodel_instance, _):
    """
    get_backend_entity for DummyModel DbNode.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    djnode_instance = DjangoSchemaDbNode(
        id=dbmodel_instance.id,
        type=dbmodel_instance.type,
        process_type=dbmodel_instance.process_type,
        uuid=dbmodel_instance.uuid,
        ctime=dbmodel_instance.ctime,
        mtime=dbmodel_instance.mtime,
        label=dbmodel_instance.label,
        description=dbmodel_instance.description,
        dbcomputer_id=dbmodel_instance.dbcomputer_id,
        user_id=dbmodel_instance.user_id,
        public=dbmodel_instance.public,
        nodeversion=dbmodel_instance.nodeversion)

    try:
        plugin_type = get_plugin_type_from_type_string(djnode_instance.type)
    except DbContentError:
        raise DbContentError("The type name of node with pk= {} is "
                             "not valid: '{}'".format(djnode_instance.pk, djnode_instance.type))

    plugin_class = load_plugin(plugin_type, safe=True)
    return plugin_class(dbnode=djnode_instance)


@get_backend_entity.register(DummySchemaDbAuthInfo)
def _(dbmodel_instance, backend_instance):
    """
    get_backend_entity for DummyModel DbAuthInfo.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    djauthinfo_instance = DjangoSchemaDbAuthInfo(
        id=dbmodel_instance.id,
        aiidauser_id=dbmodel_instance.aiidauser_id,
        dbcomputer_id=dbmodel_instance.dbcomputer_id,
        metadata=dbmodel_instance._metadata,  # pylint: disable=protected-access
        auth_params=dbmodel_instance.auth_params,
        enabled=dbmodel_instance.enabled,
    )
    return authinfo.DjangoAuthInfo.from_dbmodel(djauthinfo_instance, backend_instance)
