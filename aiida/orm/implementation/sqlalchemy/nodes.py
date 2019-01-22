# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.sqlalchemy.models import node as models

from .. import BackendNode, BackendNodeCollection
from . import entities
from . import utils


class SqlaNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """SQLA Node backend entity"""

    MODEL_CLASS = models.DbNode
    EXTRA_CLASS = models.DbExtra


    # TODO: check how many parameters we want to expose in the init
    # and if we need to define here some defaults
    def __init__(self, backend, type, process_type, label, description):
        super(SqlaNode, self).__init__(backend)
        self._dbmodel = utils.ModelWrapper(
            models.DbNode(
                type=type,
                process_type=process_type,
                label=label,
                description=description,
            ))
        self._init_backend_node()

    @property
    def uuid(self):
        """
        Get the UUID of the log entry
        """
        return six.text_type(self._dbmodel.uuid)

    def process_type(self):
        """
        The node process_type

        :return: the process type
        """

    def nodeversion(self):
        """
        Get the version number for this node

        :return: the version number
        :rtype: int
        """
        self._ensure_model_uptodate(attribute_names=['nodeversion'])
        return self._dbmodel.nodeversion

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['ctime'])
        return self._dbmodel.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        self._ensure_model_uptodate(attribute_names=['mtime'])
        return self._dbmodel.mtime

    @property
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        # Type is immutable so no need to ensure the model is up to date
        return self._dbmodel.type

    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """
        from aiida import orm

        self._ensure_model_uptodate(attribute_names=['dbcomputer'])
        if self._dbmodel.dbcomputer is None:
            return None

        return orm.Computer.from_backend_entity(self.backend.computers.from_dbmodel(self._dbmodel.dbcomputer))

    def _set_db_computer(self, computer):
                """
        Set the computer directly inside the dbnode member, in the DB.

        DO NOT USE DIRECTLY.

        :param computer: the computer object
        """
        type_check(computer, computers.SqlaComputer)
        self._dbmodel.dbcomputer = computer.dbmodel

    def get_user(self):
        """
        Get the user.

        :return: an aiida user model object
        """
        from aiida import orm

        self._ensure_model_uptodate(attribute_names=['user'])
        backend_user = self._backend.users.from_dbmodel(self._dbmodel.user)
        return orm.User.from_backend_entity(backend_user)

    def set_user(self, user):
        """
        Set the user

        :param user: The new user
        """
        from aiida import orm

        type_check(user, orm.User)
        backend_user = user.backend_entity
        self._dbmodel.user = backend_user.dbmodel

    def _set_db_extra(self, key, value, exclusive=False):
        """
        Store extra directly in the DB, without checks.

        DO NOT USE DIRECTLY.

        :param key: key name
        :param value: key value
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).
        """
        if exclusive:
            raise NotImplementedError("exclusive=True not implemented yet in SQLAlchemy backend")

        try:
            self._dbmodel.set_extra(key, value)
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _reset_db_extras(self, new_extras):
        """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        try:
            self._dbnode.reset_extras(new_extras)
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """ 
        try:
            return utils.get_attr(self._extras(), key)
        except (KeyError, AttributeError):
            raise AttributeError("DbExtra {} does not exist".format(key))

    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        try:
            self._dbnode.del_extra(key)
        except:
            from aiida.backends.sqlalchemy import get_scoped_session
            session = get_scoped_session()
            session.rollback()
            raise

    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        extras = self._extras()
        if extras is None:
            return iter(dict().items())

        return iter(extras.items())


class SqlaNodeCollection(BackendNodeCollection):
    """The SQLA collection for nodes"""

    ENTITY_CLASS = SqlaNode
