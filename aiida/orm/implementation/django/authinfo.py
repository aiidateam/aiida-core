# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import json

from aiida.backends.djsite.db.models import DbComputer, DbAuthInfo
from aiida.orm.authinfo import AuthInfo, AuthInfoCollection
from aiida.common import exceptions
from aiida.common.utils import type_check

from . import computer as computers
from . import user as users
from . import utils


class DjangoAuthInfoCollection(AuthInfoCollection):

    def create(self, computer, user):
        """
        Create a AuthInfo given a computer and a user

        :param computer: A Computer or DbComputer instance
        :param user: A User or DbUser instance
        :return: a AuthInfo object associated to the given computer and User
        """
        return DjangoAuthInfo(self, computer, user)

    def get(self, computer, user):
        """
        Return a AuthInfo given a computer and a user

        :param computer: A Computer or DbComputer instance
        :param user: A User or DbUser instance
        :return: a AuthInfo object associated to the given computer and User, if any
        :raise NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
             more than once to use the computer! Should never happen
        """
        from django.core.exceptions import (ObjectDoesNotExist,
                                            MultipleObjectsReturned)

        try:
            authinfo = DbAuthInfo.objects.get(
                # converts from name, Computer or DbComputer instance to
                # a DbComputer instance
                dbcomputer=DbComputer.get_dbcomputer(computer),
                aiidauser=user.id)

            return self._from_dbmodel(authinfo)
        except ObjectDoesNotExist:
            raise exceptions.NotExistent(
                "The aiida user {} is not configured to use computer {}".format(
                    user.email, computer.name))
        except MultipleObjectsReturned:
            raise exceptions.ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    user.email, computer.name))

    def _from_dbmodel(self, dbmodel):
        return DjangoAuthInfo._from_dbmodel(self, dbmodel)


class DjangoAuthInfo(AuthInfo):
    """
    AuthInfo implementation for Django
    """

    @classmethod
    def _from_dbmodel(cls, backend, dbmodel):
        type_check(dbmodel, DbAuthInfo)
        authinfo = cls.__new__(cls)
        super(DjangoAuthInfo, authinfo).__init__(backend)
        authinfo._dbauthinfo = utils.ModelWrapper(dbmodel)
        return authinfo

    def __init__(self, backend, computer, user):
        """
        Construct a DjangoAuthInfo

        """
        from aiida.orm.computer import Computer

        super(DjangoAuthInfo, self).__init__(backend)
        type_check(user, users.DjangoUser)

        # Takes care of always getting a Computer instance from a DbComputer, Computer or string
        dbcomputer = Computer.get(computer).dbcomputer

        self._dbauthinfo = utils.ModelWrapper(
            DbAuthInfo(dbcomputer=dbcomputer, aiidauser=user.dbuser))

    @property
    def dbauthinfo(self):
        return self._dbauthinfo._model

    @property
    def is_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
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
        return computers.Computer.get(self._dbauthinfo.dbcomputer)

    @property
    def user(self):
        return self._backend.users._from_dbmodel(self._dbauthinfo.aiidauser)

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
