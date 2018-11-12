# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Authinfo objects and functions"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.transport import TransportFactory
from aiida.common.exceptions import (ConfigurationError, MissingPluginError)
from .backends import construct_backend
from . import computers
from . import entities
from . import users

__all__ = ('AuthInfo',)


class AuthInfo(entities.Entity):
    """
    Base class to map a DbAuthInfo, that contains computer configuration
    specific to a given user (authorization info and other metadata, like
    how often to check on a given computer etc.)
    """

    class Collection(entities.Entity.Collection):
        """The collection of AuthInfo entries."""

        def find(self, computer, user):
            """
            Get an authinfo for a given computer and user combination

            :param computer: the computer to get the authinfo for
            :type computer: :class:`aiida.orm.Computer`
            :param user: the user to ge the authinfo for
            :type user: :class:`aiida.orm.User`
            :rtype: :class:`aiida.orm.AuthInfo`
            """
            return [
                AuthInfo.from_backend_entity(self._backend.authinfos.get(computer.backend_entity, user.backend_entity))
            ]

        def delete(self, authinfo_id):
            """
            Remove an AuthInfo from the collection with the given id
            :param authinfo_id: The ID of the authinfo to delete
            """
            self._backend.authinfos.delete(authinfo_id)

    def __init__(self, computer, user, backend=None):
        """
        Create a AuthInfo given a computer and a user

        :param computer: a Computer instance
        :param user: a User instance
        :return: an AuthInfo object associated with the given computer and user
        """
        backend = backend or construct_backend()
        model = backend.authinfos.create(computer=computer.backend_entity, user=user.backend_entity)
        super(AuthInfo, self).__init__(model)

    @property
    def enabled(self):
        """
        Is the computer enabled for this user?

        :rtype: bool
        """
        return self._backend_entity.enabled

    @enabled.setter
    def enabled(self, enabled):
        """
        Set the enabled state for the computer
        """
        self._backend_entity.enabled = enabled

    @property
    def computer(self):
        return computers.Computer.from_backend_entity(self._backend_entity.computer)

    @property
    def user(self):
        return users.User.from_backend_entity(self._backend_entity.user)

    def is_stored(self):
        """
        Is it already stored or not?

        :return: Boolean
        """
        return self._backend_entity.is_stored()

    def get_auth_params(self):
        """
        Get the dictionary of auth_params

        :return: a dictionary
        """
        return self._backend_entity.get_auth_params()

    def set_auth_params(self, auth_params):
        """
        Set the dictionary of auth_params

        :param auth_params: a dictionary with the new auth_params
        """
        self._backend_entity.set_auth_params(auth_params)

    def get_metadata(self):
        """
        Get the metadata dictionary

        :return: a dictionary
        """
        return self._backend_entity.get_metadata()

    def set_metadata(self, metadata):
        """
        Replace the metadata dictionary in the DB with the provided dictionary
        """
        self._backend_entity.set_metadata(metadata)

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

        return "AuthInfo for {} on {} [DISABLED]".format(self.user.email, self.computer.name)

    def get_transport(self):
        """
        Return a configured transport to connect to the computer.
        """
        computer = self.computer
        try:
            this_transport_class = TransportFactory(computer.get_transport_type())
        except MissingPluginError as exc:
            raise ConfigurationError('No transport found for {} [type {}], message: {}'.format(
                computer.hostname, computer.get_transport_type(), exc))

        params = dict(list(computer.get_transport_params().items()) + list(self.get_auth_params().items()))
        return this_transport_class(machine=computer.hostname, **params)
