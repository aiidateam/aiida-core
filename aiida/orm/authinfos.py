# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the `AuthInfo` ORM class."""

from aiida.common import exceptions
from aiida.plugins import TransportFactory
from aiida.manage.manager import get_manager
from . import entities
from . import users

__all__ = ('AuthInfo',)


class AuthInfo(entities.Entity):
    """ORM class that models the authorization information that allows a `User` to connect to a `Computer`."""

    class Collection(entities.Collection):
        """The collection of `AuthInfo` entries."""

        def delete(self, pk):
            """Delete an entry from the collection.

            :param pk: the pk of the entry to delete
            """
            self._backend.authinfos.delete(pk)

    PROPERTY_WORKDIR = 'workdir'

    def __init__(self, computer, user, backend=None):
        """Create an `AuthInfo` instance for the given computer and user.

        :param computer: a `Computer` instance
        :type computer: :class:`aiida.orm.Computer`

        :param user: a `User` instance
        :type user: :class:`aiida.orm.User`

        :rtype: :class:`aiida.orm.authinfos.AuthInfo`
        """
        backend = backend or get_manager().get_backend()
        model = backend.authinfos.create(computer=computer.backend_entity, user=user.backend_entity)
        super().__init__(model)

    def __str__(self):
        if self.enabled:
            return 'AuthInfo for {} on {}'.format(self.user.email, self.computer.name)

        return 'AuthInfo for {} on {} [DISABLED]'.format(self.user.email, self.computer.name)

    @property
    def enabled(self):
        """Return whether this instance is enabled.

        :return: True if enabled, False otherwise
        :rtype: bool
        """
        return self._backend_entity.enabled

    @enabled.setter
    def enabled(self, enabled):
        """Set the enabled state

        :param enabled: boolean, True to enable the instance, False to disable it
        """
        self._backend_entity.enabled = enabled

    @property
    def computer(self):
        """Return the computer associated with this instance.

        :rtype: :class:`aiida.orm.computers.Computer`
        """
        from . import computers  # pylint: disable=cyclic-import
        return computers.Computer.from_backend_entity(self._backend_entity.computer)

    @property
    def user(self):
        """Return the user associated with this instance.

        :rtype: :class:`aiida.orm.users.User`
        """
        return users.User.from_backend_entity(self._backend_entity.user)

    def get_auth_params(self):
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        :rtype: dict
        """
        return self._backend_entity.get_auth_params()

    def set_auth_params(self, auth_params):
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """
        self._backend_entity.set_auth_params(auth_params)

    def get_metadata(self):
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        :rtype: dict
        """
        return self._backend_entity.get_metadata()

    def set_metadata(self, metadata):
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        :type metadata: dict
        """
        self._backend_entity.set_metadata(metadata)

    def get_workdir(self):
        """Return the working directory.

        If no explicit work directory is set for this instance, the working directory of the computer will be returned.

        :return: the working directory
        :rtype: str
        """
        try:
            return self.get_metadata()[self.PROPERTY_WORKDIR]
        except KeyError:
            return self.computer.get_workdir()

    def get_transport(self):
        """Return a fully configured transport that can be used to connect to the computer set for this instance.

        :rtype: :class:`aiida.transports.Transport`
        """
        computer = self.computer
        transport_type = computer.get_transport_type()

        try:
            transport_class = TransportFactory(transport_type)
        except exceptions.EntryPointError as exception:
            raise exceptions.ConfigurationError(
                'transport type `{}` could not be loaded: {}'.format(transport_type, exception)
            )

        return transport_class(machine=computer.hostname, **self.get_auth_params())
