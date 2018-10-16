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
import abc
import six

from aiida.transport import TransportFactory
from aiida.common.exceptions import (ConfigurationError, MissingPluginError)
from .backend import Collection, CollectionEntry

__all__ = ['AuthInfo', 'AuthInfoCollection']


@six.add_metaclass(abc.ABCMeta)
class AuthInfoCollection(Collection):
    """The collection of AuthInfo entries."""

    @abc.abstractmethod
    def create(self, computer, user):
        """
        Create a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: a AuthInfo object associated to the given computer and user
        """
        pass

    @abc.abstractmethod
    def remove(self, authinfo_id):
        """
        Remove an AuthInfo from the collection with the given id
        :param authinfo_id: The ID of the authinfo to delete
        """
        pass

    @abc.abstractmethod
    def get(self, computer, user):
        """
        Return a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: a AuthInfo object associated to the given computer and user
        :raise NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
            more than once to use the computer! Should never happen
        """
        pass


@six.add_metaclass(abc.ABCMeta)
class AuthInfo(CollectionEntry):
    """
    Base class to map a DbAuthInfo, that contains computer configuration
    specific to a given user (authorization info and other metadata, like
    how often to check on a given computer etc.)
    """

    def pk(self):
        """
        Return the principal key in the DB.
        """
        return self.id

    @abc.abstractproperty
    def id(self):
        """
        Return the ID in the DB.
        """
        pass

    @abc.abstractproperty
    def enabled(self):
        """
        Is the computer enabled for this user?

        :return: Boolean
        """
        pass

    @enabled.setter
    def enabled(self, value):
        """
        Set the enabled state for the computer

        :return: Boolean
        """
        pass

    @abc.abstractproperty
    def computer(self):
        pass

    @abc.abstractproperty
    def user(self):
        pass

    @abc.abstractproperty
    def is_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
        """
        pass

    @abc.abstractmethod
    def get_auth_params(self):
        """
        Get the dictionary of auth_params

        :return: a dictionary
        """
        pass

    @abc.abstractmethod
    def set_auth_params(self, auth_params):
        """
        Set the dictionary of auth_params

        :param auth_params: a dictionary with the new auth_params
        """
        pass

    @abc.abstractmethod
    def get_metadata(self):
        """
        Get the metadata dictionary

        :return: a dictionary
        """
        pass

    @abc.abstractmethod
    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        pass

    def get_workdir(self):
        """
        Get the workdir; defaults to the value of the corresponding computer, if not explicitly set

        :return: a string
        """
        metadata = self.get_metadata()

        try:
            return metadata['workdir']
        except KeyError:
            return self.computer.get_workdir()

    def __str__(self):
        if self.enabled:
            return "AuthInfo for {} on {}".format(self.user.email, self.computer.name)
        else:
            return "AuthInfo for {} on {} [DISABLED]".format(self.user.email, self.computer.name)

    def get_transport(self):
        """
        Return a configured transport to connect to the computer.
        """
        computer = self.computer
        try:
            ThisTransport = TransportFactory(computer.get_transport_type())
        except MissingPluginError as exc:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                computer.hostname, computer.get_transport_type(), exc))

        params = dict(list(computer.get_transport_params().items()) + list(self.get_auth_params().items()))
        return ThisTransport(machine=computer.hostname, **params)
