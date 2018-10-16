# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import json

from aiida.backends.djsite.db.models import DbAuthInfo
from aiida.common import exceptions
from aiida.common.utils import type_check
from aiida.orm.authinfo import AuthInfo, AuthInfoCollection

from . import computer as computers
from . import user as users
from . import utils


class DjangoAuthInfoCollection(AuthInfoCollection):

    def create(self, computer, user):
        """
        Create a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        """
        return DjangoAuthInfo(self.backend, computer, user)

    def get(self, computer, user):
        """
        Return a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        :raise NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
            more than once to use the computer! Should never happen
        """
        from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

        try:
            authinfo = DbAuthInfo.objects.get(dbcomputer=computer.id, aiidauser=user.id)
            return self.from_dbmodel(authinfo)
        except ObjectDoesNotExist:
            raise exceptions.NotExistent(
                "The aiida user {} is not configured to use computer {}".format(
                    user.email, computer.name))
        except MultipleObjectsReturned:
            raise exceptions.ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    user.email, computer.name))

    def remove(self, authinfo_id):
        from django.core.exceptions import ObjectDoesNotExist
        try:
            DbAuthInfo.objects.get(pk=authinfo_id).delete()
        except ObjectDoesNotExist:
            raise exceptions.NotExistent("AuthInfo with id '{}' not found".format(authinfo_id))

    def from_dbmodel(self, dbmodel):
        return DjangoAuthInfo.from_dbmodel(dbmodel, self.backend)


class DjangoAuthInfo(AuthInfo):
    """AuthInfo implementation for Django."""

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        type_check(dbmodel, DbAuthInfo)
        authinfo = cls.__new__(cls)
        super(DjangoAuthInfo, authinfo).__init__(backend)
        authinfo._dbauthinfo = utils.ModelWrapper(dbmodel)
        return authinfo

    def __init__(self, backend, computer, user):
        """
        Construct a DjangoAuthInfo.

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        """
        super(DjangoAuthInfo, self).__init__(backend)
        type_check(user, users.DjangoUser)
        self._dbauthinfo = utils.ModelWrapper(DbAuthInfo(dbcomputer=computer.dbcomputer, aiidauser=user.dbuser))

    @property
    def dbauthinfo(self):
        return self._dbauthinfo._model

    @property
    def is_stored(self):
        """
        Return whether the AuthInfo is stored

        :return: True if stored, False otherwise
        """
        return self._dbauthinfo.is_saved()

    @property
    def id(self):
        return self._dbauthinfo.id

    @property
    def enabled(self):
        return self._dbauthinfo.enabled

    @enabled.setter
    def enabled(self, value):
        self._dbauthinfo.enabled = value

    @property
    def computer(self):
        return self.backend.computers.from_dbmodel(self._dbauthinfo.dbcomputer)

    @property
    def user(self):
        return self._backend.users.from_dbmodel(self._dbauthinfo.aiidauser)

    def get_auth_params(self):
        """
        Get the auth_params dictionary from the DB

        :return: a dictionary
        """
        try:
            return json.loads(self._dbauthinfo.auth_params)
        except ValueError:
            email = self._dbauthinfo.aiidauser.email
            hostname = self._dbauthinfo.dbcomputer.hostname
            raise exceptions.DbContentError(
                "Error while reading auth_params for dbauthinfo, aiidauser={}, computer={}".format(email, hostname))

    def set_auth_params(self, auth_params):
        """
        Replace the auth_params dictionary in the DB with the provided dictionary
        """
        import json

        # Raises ValueError if data is not JSON-serializable
        self._dbauthinfo.auth_params = json.dumps(auth_params)

    def get_metadata(self):
        """
        Get the metadata dictionary from the DB

        :return: a dictionary
        """
        import json

        try:
            return json.loads(self._dbauthinfo.metadata)
        except ValueError:
            raise exceptions.DbContentError(
                "Error while reading metadata for dbauthinfo, aiidauser={}, computer={}".format(
                    self.aiidauser.email, self.dbcomputer.hostname))

    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        # Raises ValueError if data is not JSON-serializable
        self._dbauthinfo.metadata = json.dumps(metadata)

    def store(self):
        """
        Store the AuthInfo (possibly updating values if changed)

        :return: the AuthInfo instance
        """
        self._dbauthinfo.save()
        return self
