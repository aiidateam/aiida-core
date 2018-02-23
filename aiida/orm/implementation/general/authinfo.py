# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import ABCMeta, abstractmethod, abstractproperty

import logging
import os

from aiida.transport import Transport, TransportFactory
from aiida.scheduler import Scheduler, SchedulerFactory

from aiida.common.exceptions import (
    ConfigurationError, DbContentError,
    MissingPluginError, ValidationError)

from aiida.common.utils import classproperty
from aiida.common.utils import abstractclassmethod, abstractstaticmethod


class AbstractAuthInfo(object):
    """
    Base class to map a DbAuthInfo, that contains computer configuration
    specific to a given user (authorization info and other metadata, like
    how often to check on a given computer etc.)
    """
    _logger = logging.getLogger(__name__)

    @classmethod
    def get(cls, computer, user):
        """
        Return a AuthInfo given a computer and a user

        :param computer: A Computer or DbComputer instance
        :param user: A User or DbUser instance
        :return: a AuthInfo object associated to the given computer and User, if any
        :raise NotExistent: if the user is not configured to use computer
        :raise  MultipleResultsFound: if the user is configured more than once to use the
             computer! Should never happen
        """
        from aiida.backends.utils import get_dbauthinfo

        dbauthinfo = get_dbauthinfo(computer=computer, aiidauser=user)
        return cls(dbauthinfo=dbauthinfo)

    @abstractmethod
    def __init__(self, **kwargs):
        """
        The init needs to define the self.dbauthinfo object
        """
        pass

    @property
    def dbauthinfo(self):
        return self._dbauthinfo

    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying with Django.
        Be careful, though, not to pass it to a wrong field! This only returns the
        local DB principal key value.
        """
        return self.id

    @abstractproperty
    def pk(self):
        """
        Return the principal key in the DB.
        """
        return self.id

    @abstractproperty
    def id(self):
        """
        Return the ID in the DB.
        """
        return self.dbauthinfo.id

    @property
    def logger(self):
        """
        Return the logger
        :return:
        """
        return self._logger

    @property
    def enabled(self):
        """
        Is the computer enabled for this user?

        :return: Boolean
        """
        return self.dbauthinfo.enabled

    @enabled.setter
    def enabled(self, value):
        """
        Set the enabled state for the computer

        :return: Boolean
        """
        self.dbauthinfo.enabled = value
        if not self.to_be_stored:
            self.store()

    @property
    def computer(self):
        from aiida.orm.computer import Computer
        return Computer.get(self.dbauthinfo.dbcomputer)

    @property
    def user(self):
        from aiida.orm.user import User
        return User.get(email = self.dbauthinfo.aiidauser.email)

    @abstractproperty
    def to_be_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
        """
        pass

    def get_auth_params(self):
        """
        Get the dictionary of auth_params stored in the DB

        :return: a dictionary
        """
        return self.dbauthinfo.get_auth_params()

    def set_auth_params(self, auth_params):
        """
        Set the dictionary of auth_params stored in the DB

        :param auth_params: a dictionary with the new auth_params
        """
        self.dbauthinfo.set_auth_params(auth_params)

    def get_metadata(self):
        """
        Get the metadata dictionary from the DB

        :return: a dictionary
        """
        return self.dbauthinfo.get_metadata()

    def get_workdir(self):
        """
        Get the workdir; defaults to the value of the corresponding computer, if not explicitly set

        :return: a string
        """
        return self.dbauthinfo.get_workdir()

    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        return self.dbauthinfo.set_metadata(metadata=metadata)

    def __str__(self):
        if self.enabled:
            return "AuthInfo for {} on {}".format(self.aiidauser.email, self.dbcomputer.name)
        else:
            return "AuthInfo for {} on {} [DISABLED]".format(self.aiidauser.email, self.dbcomputer.name)

    def get_transport(self):
        """
        Return a configured transport to connect to the computer.
        """
        from aiida.orm.computer import Computer
        try:
            ThisTransport = TransportFactory(self.computer.get_transport_type())
        except MissingPluginError as e:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                self.computer.hostname, self.computer.get_transport_type(), e.message))

        params = dict(self.computer.get_transport_params().items() +
                      self.get_auth_params().items())
        return ThisTransport(machine=self.computer.hostname, **params)