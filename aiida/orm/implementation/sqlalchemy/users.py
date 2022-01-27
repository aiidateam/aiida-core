# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQLA user"""
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.orm.implementation.users import BackendUser, BackendUserCollection

from . import entities, utils

__all__ = ('SqlaUserCollection', 'SqlaUser')


class SqlaUser(entities.SqlaModelEntity[DbUser], BackendUser):
    """SQLA user"""

    MODEL_CLASS = DbUser

    def __init__(self, backend, email, first_name, last_name, institution):
        # pylint: disable=too-many-arguments
        super().__init__(backend)
        self._dbmodel = utils.ModelWrapper(
            DbUser(email=email, first_name=first_name, last_name=last_name, institution=institution)
        )

    @property
    def email(self):
        return self._dbmodel.email

    @email.setter
    def email(self, email):
        self._dbmodel.email = email

    @property
    def first_name(self):
        return self._dbmodel.first_name

    @first_name.setter
    def first_name(self, first_name):
        self._dbmodel.first_name = first_name

    @property
    def last_name(self):
        return self._dbmodel.last_name

    @last_name.setter
    def last_name(self, last_name):
        self._dbmodel.last_name = last_name

    @property
    def institution(self):
        return self._dbmodel.institution

    @institution.setter
    def institution(self, institution):
        self._dbmodel.institution = institution


class SqlaUserCollection(BackendUserCollection):
    """Collection of SQLA Users"""

    ENTITY_CLASS = SqlaUser

    def create(self, email, first_name='', last_name='', institution=''):  # pylint: disable=arguments-differ
        """
        Create a user with the provided email address

        :return: A new user object
        :rtype: :class:`aiida.orm.User`
        """
        # pylint: disable=abstract-class-instantiated
        return SqlaUser(self.backend, email, first_name, last_name, institution)
