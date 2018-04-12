# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.authinfo import AbstractAuthInfoCollection, AbstractAuthInfo
from aiida.common.exceptions import ConfigurationError, NotExistent
from . import user as users


class SqlaAlchemyAuthInfoCollection(AbstractAuthInfoCollection):
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
        from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
        from aiida.backends.sqlalchemy import get_scoped_session
        session = get_scoped_session()
        from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

        try:
            authinfo = session.query(DbAuthInfo).filter_by(
                dbcomputer_id=computer.id,
                aiidauser_id=user.id,
            ).one()
        except NoResultFound:
            raise NotExistent(
                "The aiida user {} is not configured to use computer {}".format(
                    user.email, computer.name))
        except MultipleResultsFound:
            raise ConfigurationError(
                "The aiida user {} is configured more than once to use "
                "computer {}! Only one configuration is allowed".format(
                    user.email, computer.name))


from . import user as users


class AuthInfo(AbstractAuthInfo):
    """
    AuthInfo implementation for SQLAlchemy
    """

    def __init__(self, **kwargs):
        """
        Set the dbauthinfo Db Instance

        :param dbauthinfo:
        """
        from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
        from aiida.orm.computer import Computer
        from aiida.orm.backend import construct_backend

        self._backend = construct_backend()

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
            dbuser = self._backend.users.get(email=user.email)._dbuser
            self._dbauthinfo = DbAuthInfo(dbcomputer=dbcomputer, aiidauser=dbuser)

    @property
    def to_be_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
        """
        return self._dbauthinfo.id is None

    def store(self):
        """
        Store the authinfo

        :return: the AuthInfo instance
        """
        from sqlalchemy.exc import SQLAlchemyError

        try:
            self._dbauthinfo.save(commit=True)
        except SQLAlchemyError:
            raise ValueError("Integrity error while storing the DbAuthInfo")

        return self
