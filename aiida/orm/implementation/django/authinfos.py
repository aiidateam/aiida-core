# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementations for the `AuthInfo` entity and collection."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.djsite.db.models import DbAuthInfo
from aiida.common import exceptions
from aiida.common import json
from aiida.common.lang import type_check

from ..authinfos import BackendAuthInfo, BackendAuthInfoCollection
from . import entities
from . import utils


class DjangoAuthInfo(entities.DjangoModelEntity[DbAuthInfo], BackendAuthInfo):
    """AuthInfo implementation for Django."""

    MODEL_CLASS = DbAuthInfo

    @classmethod
    def get_dbmodel_attribute_name(cls, attr_name):
        """Return the name of the auth info attribute as it is known to the database model.

        This is essentially a mapping because the `type_string` attribute is called `type` on the database model class.

        :return: name of the backend `attribute` as defined on the database model class
        """
        if attr_name == 'type_string':
            return 'type'

        return super(DjangoAuthInfo, cls).get_dbmodel_attribute_name(attr_name)

    def __init__(self, backend, computer, user):
        """
        Construct a DjangoAuthInfo.

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        """
        from . import computers
        from . import users
        super(DjangoAuthInfo, self).__init__(backend)
        type_check(user, users.DjangoUser)
        type_check(computer, computers.DjangoComputer)
        self._dbmodel = utils.ModelWrapper(DbAuthInfo(dbcomputer=computer.dbmodel, aiidauser=user.dbmodel))

    @property
    def is_stored(self):
        """Return whether the `AuthInfo` is stored

        :return: True if stored, False otherwise
        """
        return self._dbmodel.is_saved()

    @property
    def id(self):
        return self._dbmodel.id

    @property
    def enabled(self):
        return self._dbmodel.enabled

    @enabled.setter
    def enabled(self, enabled):
        self._dbmodel.enabled = enabled

    @property
    def computer(self):
        return self.backend.computers.from_dbmodel(self._dbmodel.dbcomputer)

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbmodel.aiidauser)

    def get_auth_params(self):
        """
        Get the auth_params dictionary from the DB

        :return: a dictionary
        """
        try:
            return json.loads(self._dbmodel.auth_params)
        except ValueError:
            email = self._dbmodel.aiidauser.email
            hostname = self._dbmodel.dbcomputer.hostname
            raise exceptions.DbContentError(
                "Error while reading auth_params for dbauthinfo, aiidauser={}, computer={}".format(email, hostname))

    def set_auth_params(self, auth_params):
        """
        Replace the auth_params dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbmodel.auth_params = json.dumps(auth_params)

    def get_metadata(self):
        """
        Get the metadata dictionary from the DB

        :return: a dictionary
        """
        try:
            return json.loads(self._dbmodel.metadata)
        except ValueError:
            raise exceptions.DbContentError(
                "Error while reading metadata for dbauthinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.email, self.dbcomputer.hostname))

    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbmodel.metadata = json.dumps(metadata)

    def store(self):
        """
        Store the AuthInfo (possibly updating values if changed)

        :return: the AuthInfo instance
        """
        self._dbmodel.save()
        return self


class DjangoAuthInfoCollection(BackendAuthInfoCollection):
    """Collection of AuthInfo instances."""

    ENTITY_CLASS = DjangoAuthInfo

    def get(self, computer, user):
        """
        Return a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        :raise aiida.common.NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
            more than once to use the computer! Should never happen
        """
        # pylint: disable=import-error,no-name-in-module
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

        try:
            authinfo = DbAuthInfo.objects.get(dbcomputer=computer.id, aiidauser=user.id)
            return self.from_dbmodel(authinfo)
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("The aiida user {} is not configured to use computer {}".format(
                user.email, computer.name))
        except MultipleObjectsReturned:
            raise exceptions.ConfigurationError("The aiida user {} is configured more than once to use "
                                                "computer {}! Only one configuration is allowed".format(
                                                    user.email, computer.name))

    def delete(self, authinfo_id):
        """Delete an `AuthInfo` entry from the collection and database.

        :param authinfo_id: the id of the entity
        """
        # pylint: disable=import-error,no-name-in-module
        from django.core.exceptions import ObjectDoesNotExist
        try:
            DbAuthInfo.objects.get(pk=authinfo_id).delete()
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("AuthInfo with id '{}' not found".format(authinfo_id))
