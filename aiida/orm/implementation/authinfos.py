# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for authinfo backend classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import six

from . import backends

__all__ = ('BackendAuthInfo', 'BackendAuthInfoCollection')


@six.add_metaclass(abc.ABCMeta)
class BackendAuthInfo(backends.BackendEntity):
    """
    Base class for backend authorization information which contains computer configuration
    specific to a given user (authorization info and other metadata, like
    how often to check on a given computer etc.)
    """

    METADATA_WORKDIR = 'workdir'

    def pk(self):
        """
        Return the principal key in the DB.
        """
        return self.id

    @abc.abstractproperty
    def id(self):  # pylint: disable=invalid-name
        """
        Return the ID in the DB.
        """

    @abc.abstractproperty
    def enabled(self):
        """
        Is the computer enabled for this user?

        :rtype: bool
        """

    @enabled.setter
    def enabled(self, value):
        """
        Set the enabled state for the computer

        :return: Boolean
        """

    @abc.abstractproperty
    def computer(self):
        """
        The computer that this authinfo relates to

        :return: The corresponding computer
        :rtype: :class:`aiida.orm.Computer`
        """

    @abc.abstractproperty
    def user(self):
        """
        The user that this authinfo relates to

        :return: The corresponding user
        :rtype: :class:`aiida.orm.User`
        """

    @abc.abstractproperty
    def is_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
        :rtype: bool
        """

    @abc.abstractmethod
    def get_auth_params(self):
        """
        Get the dictionary of auth_params

        :return: a dictionary
        """

    @abc.abstractmethod
    def set_auth_params(self, auth_params):
        """
        Set the dictionary of auth_params

        :param auth_params: a dictionary with the new auth_params
        """

    @abc.abstractmethod
    def get_metadata(self):
        """
        Get the metadata dictionary

        :return: a dictionary
        """

    @abc.abstractmethod
    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """

    def get_property(self, name):
        try:
            return self.get_metadata()[name]
        except KeyError:
            raise ValueError('Unknown property: {}'.format(name))

    def set_property(self, name, value):
        metadata = self.get_metadata()
        metadata[name] = value
        self.set_metadata(metadata)


@six.add_metaclass(abc.ABCMeta)
class BackendAuthInfoCollection(backends.BackendCollection[BackendAuthInfo]):
    """The collection of AuthInfo entries."""

    ENTITY_CLASS = BackendAuthInfo

    @abc.abstractmethod
    def delete(self, authinfo_id):
        """
        Remove an AuthInfo from the collection with the given id
        :param authinfo_id: The ID of the authinfo to delete
        """

    @abc.abstractmethod
    def get(self, computer, user):
        """
        Return a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: a AuthInfo object associated to the given computer and user
        :raise aiida.common.NotExistent: if the user is not configured to use computer
        :raise sqlalchemy.orm.exc.MultipleResultsFound: if the user is configured
            more than once to use the computer! Should never happen
        """
