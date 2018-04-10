# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.djsite.db.models import DbComputer, DbAuthInfo
from aiida.orm.authinfo import AbstractAuthInfo, AbstractAuthInfoCollection
from aiida.common.exceptions import ConfigurationError, NotExistent
from aiida.common.utils import type_check

from . import user as users


class DjangoAuthInfoCollection(AbstractAuthInfoCollection):

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
            raise NotExistent(
                "The aiida user {} is not configured to use computer {}".format(
                    user.email, computer.name))
        except MultipleObjectsReturned:
            raise ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    user.email, computer.name))

    def _from_dbmodel(self, dbmodel):
        type_check(dbmodel, DbAuthInfo)
        return DjangoAuthInfo._from_dbmodel(self, dbmodel)


class DjangoAuthInfo(AbstractAuthInfo):
    """
    AuthInfo implementation for Django
    """

    @classmethod
    def _from_dbmodel(cls, backend, dbmodel):
        authinfo = cls.__new__()
        super(DjangoAuthInfo, authinfo)._from_dbmodel(backend)
        authinfo._dbauthinfo = dbmodel
        return authinfo

    def __init__(self, backend, computer, user):
        """
        Set the dbauthinfo Db Instance

        :param dbauthinfo:
        """
        from aiida.orm.computer import Computer

        super(DjangoAuthInfo, self).__init__(backend)
        type_check(user, users.DjangoUser)

        # Takes care of always getting a Computer instance from a DbComputer, Computer or string
        dbcomputer = Computer.get(computer).dbcomputer
        # user.email exists both for DbUser and User, so I'm robust w.r.t. the type of what I get
        self._dbauthinfo = DbAuthInfo(dbcomputer=dbcomputer, aiidauser=user._dbuser)

    @property
    def to_be_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
        """
        return (self._dbauthinfo.pk is None)

    def store(self):
        """
        Store the AuthInfo (possibly updating values if changed)

        :return: the AuthInfo instance
        """
        from django.db import IntegrityError, transaction

        try:
            # transactions are needed here for Postgresql:
            # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
            sid = transaction.savepoint()
            self._dbauthinfo.save()
            transaction.savepoint_commit(sid)
        except IntegrityError:
            transaction.savepoint_rollback(sid)
            raise ValueError(
                "Integrity error while storing the DbAuthInfo")

        return self
