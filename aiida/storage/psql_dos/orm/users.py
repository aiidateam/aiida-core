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
from aiida.orm.implementation.users import BackendUser, BackendUserCollection
from aiida.storage.psql_dos.models.user import DbUser

from . import entities, utils


class SqlaUser(entities.SqlaModelEntity[DbUser], BackendUser):
    """SQLA user"""

    MODEL_CLASS = DbUser

    def __init__(self, backend, email, first_name, last_name, institution):
        # pylint: disable=too-many-arguments
        super().__init__(backend)
        self._model = utils.ModelWrapper(
            self.MODEL_CLASS(email=email, first_name=first_name, last_name=last_name, institution=institution), backend
        )

    @property
    def email(self):
        return self.model.email

    @email.setter
    def email(self, email):
        self.model.email = email

    @property
    def first_name(self):
        return self.model.first_name

    @first_name.setter
    def first_name(self, first_name):
        self.model.first_name = first_name

    @property
    def last_name(self):
        return self.model.last_name

    @last_name.setter
    def last_name(self, last_name):
        self.model.last_name = last_name

    @property
    def institution(self):
        return self.model.institution

    @institution.setter
    def institution(self, institution):
        self.model.institution = institution


class SqlaUserCollection(BackendUserCollection):
    """Collection of SQLA Users"""

    ENTITY_CLASS = SqlaUser

    def create(self, email, first_name='', last_name='', institution=''):  # pylint: disable=arguments-differ
        """ Create a user with the provided email address"""
        return self.ENTITY_CLASS(self.backend, email, first_name, last_name, institution)
