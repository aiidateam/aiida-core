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

from aiida.backends.djsite.db import models

from .. import BackendNode, BackendNodeCollection
from . import entities


class DjangoNode(entities.SqlaModelEntity[models.DbNode], BackendNode):
    """Django Node backend entity"""

    MODEL_CLASS = models.DbNode
    EXTRA_CLASS = models.DbExtra

    # TODO: check how many parameters we want to expose in the init
    # and if we need to define here some defaults
    def __init__(self, backend, type, process_type, label, description):
        # pylint: disable=too-many-arguments
        super(DjangoNode, self).__init__(backend)
        self._dbmodel = models.DbNode(
            type=type,
            process_type=process_type,
            label=label,
            description=description,
        )
        self._init_backend_node()

    @property
    def uuid(self):
        """
        Get the UUID of the log entry
        """
        return self._dbmodel.uuid

    @property
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        return self._dbmodel.type

    def get_computer(self):
        """
        Get the computer associated to the node.

        :return: the Computer object or None.
        """
        from aiida import orm

        if self._dbmodel.dbcomputer is None:
            return None

        return orm.Computer.from_backend_entity(self._backend.computers.from_dbmodel(self._dbmodel.dbcomputer))

    def _set_db_computer(self, computer):
        """
        Set the computer directly inside the dbnode member, in the DB.

        DO NOT USE DIRECTLY.

        :param computer: the computer object
        """
        type_check(computer, computers.DjangoComputer)
        self._dbmodel.dbcomputer = computer.dbmodel

    def get_user(self):
        """
        Get the user.

        :return: a User model object
        :rtype: :class:`aiida.orm.User`
        """
        from aiida import orm

        return orm.User.from_backend_entity(self._backend.users.from_dbmodel(self._dbmodel.user))

    def set_user(self, user):
        """
        Set the user

        :param user: The new user
        """
        type_check(user, user.User)
        assert user.backend == self.backend, "Passed user from different backend"
        self._dbmodel.user = user.backend_entity.dbmodel

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
        self.EXTRA_CLASS.set_value_for_node(self._dbmodel, key, value, stop_if_existing=exclusive)

    def _reset_db_extras(self, new_extras):
                """
        Resets the extras (replacing existing ones) directly in the DB

        DO NOT USE DIRECTLY!

        :param new_extras: dictionary with new extras
        """
        raise NotImplementedError("Reset of extras has not been implemented" "for Django backend.")
    
    def _get_db_extra(self, key):
        """
        Get an extra, directly from the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        :return: the key value
        :raise AttributeError: if the key does not exist
        """        
        return self.EXTRA_CLASS.get_value_for_node(dbnode=self._dbmodel, key=key)
    
    def _del_db_extra(self, key):
        """
        Delete an extra, directly on the DB.

        DO NOT USE DIRECTLY.

        :param key: key name
        """
        if not self.EXTRA_CLASS.has_key(self._dbnode, key):
            raise AttributeError("DbExtra {} does not exist".format(key))
        return self.EXTRA_CLASS.del_value_for_node(self._dbmodel, key)

    def _db_extras_items(self):
        """
        Iterator over the extras (directly in the DB!)

        DO NOT USE DIRECTLY.
        """
        extraslist = self.EXTRA_CLASS.list_all_node_elements(self._dbnode)
        for e in extraslist:
            yield (e.key, e.getvalue())

class DjangoNodeCollection(BackendNodeCollection):
    """The Django collection for nodes"""

    ENTITY_CLASS = DjangoNode
