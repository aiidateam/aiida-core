# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=cyclic-import,no-member
"""Module to get an ORM backend instance from a database model instance."""

try:  # Python3
    from functools import singledispatch
except ImportError:  # Python2
    from singledispatch import singledispatch

import aiida.backends.djsite.db.models as djmodels

__all__ = ('get_backend_entity',)


@singledispatch
def get_backend_entity(dbmodel, backend):  # pylint: disable=unused-argument
    """
    Default get_backend_entity from DbModel

    :param dbmodel: the db model instance
    """
    raise TypeError(
        'No corresponding AiiDA backend class exists for the DbModel instance {}'.format(dbmodel.__class__.__name__)
    )


@get_backend_entity.register(djmodels.DbUser)
def _(dbmodel, backend):
    """
    get_backend_entity for Django DbUser
    """
    from . import users
    return users.DjangoUser.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbGroup)
def _(dbmodel, backend):
    """
    get_backend_entity for Django DbGroup
    """
    from . import groups
    return groups.DjangoGroup.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbComputer)
def _(dbmodel, backend):
    """
    get_backend_entity for Django DbGroup
    """
    from . import computers
    return computers.DjangoComputer.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbNode)
def _(dbmodel, backend):
    """
    get_backend_entity for Django DbNode. It will return an ORM instance since
    there is not Node backend entity yet.
    """
    from . import nodes
    return nodes.DjangoNode.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbAuthInfo)
def _(dbmodel, backend):
    """
    get_backend_entity for Django DbAuthInfo
    """
    from . import authinfos
    return authinfos.DjangoAuthInfo.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbComment)
def _(dbmodel, backend):
    from . import comments
    return comments.DjangoComment.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbLog)
def _(dbmodel, backend):
    from . import logs
    return logs.DjangoLog.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(djmodels.DbUser.sa)
def _(dbmodel, backend):
    """
    get_backend_entity for DummyModel DbUser.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    from . import users
    djuser_instance = djmodels.DbUser(
        id=dbmodel.id,
        email=dbmodel.email,
        first_name=dbmodel.first_name,
        last_name=dbmodel.last_name,
        institution=dbmodel.institution
    )
    return users.DjangoUser.from_dbmodel(djuser_instance, backend)


@get_backend_entity.register(djmodels.DbGroup.sa)
def _(dbmodel, backend):
    """
    get_backend_entity for DummyModel DbGroup.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    from . import groups
    djgroup_instance = djmodels.DbGroup(
        id=dbmodel.id,
        type_string=dbmodel.type_string,
        uuid=dbmodel.uuid,
        label=dbmodel.label,
        time=dbmodel.time,
        description=dbmodel.description,
        user_id=dbmodel.user_id,
    )
    return groups.DjangoGroup.from_dbmodel(djgroup_instance, backend)


@get_backend_entity.register(djmodels.DbComputer.sa)
def _(dbmodel, backend):
    """
    get_backend_entity for DummyModel DbComputer.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    from . import computers
    djcomputer_instance = djmodels.DbComputer(
        id=dbmodel.id,
        uuid=dbmodel.uuid,
        name=dbmodel.name,
        hostname=dbmodel.hostname,
        description=dbmodel.description,
        transport_type=dbmodel.transport_type,
        scheduler_type=dbmodel.scheduler_type,
        metadata=dbmodel.metadata
    )
    return computers.DjangoComputer.from_dbmodel(djcomputer_instance, backend)


@get_backend_entity.register(djmodels.DbNode.sa)
def _(dbmodel, backend):
    """
    get_backend_entity for DummyModel DbNode.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    djnode_instance = djmodels.DbNode(
        id=dbmodel.id,
        node_type=dbmodel.node_type,
        process_type=dbmodel.process_type,
        uuid=dbmodel.uuid,
        ctime=dbmodel.ctime,
        mtime=dbmodel.mtime,
        label=dbmodel.label,
        description=dbmodel.description,
        dbcomputer_id=dbmodel.dbcomputer_id,
        user_id=dbmodel.user_id,
        attributes=dbmodel.attributes,
        extras=dbmodel.extras
    )

    from . import nodes
    return nodes.DjangoNode.from_dbmodel(djnode_instance, backend)


@get_backend_entity.register(djmodels.DbAuthInfo.sa)
def _(dbmodel, backend):
    """
    get_backend_entity for DummyModel DbAuthInfo.
    DummyModel instances are created when QueryBuilder queries the Django backend.
    """
    from . import authinfos
    djauthinfo_instance = djmodels.DbAuthInfo(
        id=dbmodel.id,
        aiidauser_id=dbmodel.aiidauser_id,
        dbcomputer_id=dbmodel.dbcomputer_id,
        metadata=dbmodel.metadata,  # pylint: disable=protected-access
        auth_params=dbmodel.auth_params,
        enabled=dbmodel.enabled,
    )
    return authinfos.DjangoAuthInfo.from_dbmodel(djauthinfo_instance, backend)


@get_backend_entity.register(djmodels.DbComment.sa)
def _(dbmodel, backend):
    """
    Convert a dbcomment to the backend entity
    """
    from . import comments
    djcomment = djmodels.DbComment(
        id=dbmodel.id,
        uuid=dbmodel.uuid,
        dbnode_id=dbmodel.dbnode_id,
        ctime=dbmodel.ctime,
        mtime=dbmodel.mtime,
        user_id=dbmodel.user_id,
        content=dbmodel.content
    )
    return comments.DjangoComment.from_dbmodel(djcomment, backend)


@get_backend_entity.register(djmodels.DbLog.sa)
def _(dbmodel, backend):
    """
    Convert a dbcomment to the backend entity
    """
    from . import logs
    djlog = djmodels.DbLog(
        id=dbmodel.id,
        time=dbmodel.time,
        loggername=dbmodel.loggername,
        levelname=dbmodel.levelname,
        dbnode_id=dbmodel.dbnode_id,
        message=dbmodel.message,
        metadata=dbmodel.metadata  # pylint: disable=protected-access
    )
    return logs.DjangoLog.from_dbmodel(djlog, backend)
