# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.implementation.general.authinfo import AbstractAuthInfo

class AuthInfo(AbstractAuthInfo):
    """
    AuthInfo implementation for Django
    """

    def __init__(self, **kwargs):
        """
        Set the dbauthinfo Db Instance

        :param dbauthinfo:
        """
        from aiida.backends.djsite.db.models import DbAuthInfo
        from aiida.orm.computer import Computer
        from aiida.orm.user import User

        try:
            self._dbauthinfo = kwargs.pop('dbauthinfo')
            if not isinstance(self._dbauthinfo, DbAuthInfo):
                raise TypeError("Expected a DbAuthInfo. Object of a different"
                                 "class was given as argument.")
            if kwargs:
                raise ValueError("If you pass a dbauthinfo parameter, "
                                 "you cannot pass any further parameter")

        except KeyError:
            # No dbauthinfo provided: create a new one with computer and user
            try:
                computer, user = (kwargs.pop('computer'), kwargs.pop('user'))
            except KeyError:
                raise ValueError("If you do not pass a dbauthinfo parameter, "
                                 "you have to pass a computer and a user parameter")
            if kwargs:
                raise ValueError("The following parameters were not recognized: {}".format(
                    ", ".format(sorted(kwargs.keys()))
                ))

            # Takes care of always getting a Computer instance from a DbComputer, Computer or string
            dbcomputer = Computer.get(computer).dbcomputer
            # user.email exists both for DbUser and User, so I'm robust w.r.t. the type of what I get
            dbuser = User.get(email=user.email).dbuser

            self._dbauthinfo = DbAuthInfo(dbcomputer=dbcomputer, aiidauser=dbuser)

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
