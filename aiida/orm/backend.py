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
from abc import abstractproperty, ABCMeta
import six

__all__ = ['Backend', 'construct_backend', 'Collection', 'CollectionEntry']

_DJANGO_BACKEND = None
_SQLA_BACKEND = None


def construct_backend(backend_type=None):
    """
    Construct a concrete backend instance based on the backend_type or use the global backend value if not specified.

    :param backend_type: get a backend instance based on the specified type (or default)
    :return: :class:`aiida.orm.backend.Backend`
    """
    if backend_type is None:
        from aiida.backends import settings
        backend_type = settings.BACKEND

    if backend_type == 'django':
        global _DJANGO_BACKEND
        if _DJANGO_BACKEND is None:
            from aiida.orm.implementation.django.backend import DjangoBackend
            _DJANGO_BACKEND = DjangoBackend()
        return _DJANGO_BACKEND
    elif backend_type == 'sqlalchemy':
        global _SQLA_BACKEND
        if _SQLA_BACKEND is None:
            from aiida.orm.implementation.sqlalchemy.backend import SqlaBackend
            _SQLA_BACKEND = SqlaBackend()
        return _SQLA_BACKEND
    else:
        raise ValueError("The specified backend {} is currently not implemented".format(backend_type))


@six.add_metaclass(ABCMeta)
class Backend(object):
    """The public interface that defines a backend factory that creates backend specific concrete objects."""

    @abstractproperty
    def logs(self):
        """
        Return the collection of log entries

        :return: the log collection
        :rtype: :class:`aiida.orm.log.Log`
        """

    @abstractproperty
    def users(self):
        """
        Return the collection of users

        :return: the users collection
        :rtype: :class:`aiida.orm.user.UserCollection`
        """

    @abstractproperty
    def authinfos(self):
        """
        Return the collection of authorisation information objects

        :return: the authinfo collection
        :rtype: :class:`aiida.orm.authinfo.AuthInfoCollection`
        """

    @abstractproperty
    def computers(self):
        """
        Return the collection of computer objects

        :return: the computers collection
        :rtype: :class:`aiida.orm.computer.ComputerCollection`
        """

    @abstractproperty
    def query_manager(self):
        """
        Return the query manager for the objects stored in the backend

        :return: The query manger
        :rtype: :class:`aiida.backends.general.abstractqueries.AbstractQueryManager`
        """


class Collection(object):
    """Container class that represents a collection of entries of a particular backend entity."""

    def __init__(self, backend):
        self._backend = backend

    @property
    def backend(self):
        """Return the backend."""
        return self._backend


class CollectionEntry(object):
    """Class that represents an entry within a collection of entries of a particular backend entity."""

    def __init__(self, backend):
        """
        :param backend: The backend instance
        :type backend: :class:`aiida.orm.backend.Backend`
        """
        if not isinstance(backend, Backend):
            raise TypeError("Must supply a backend, got '{}'".format(type(backend)))
        self._backend = backend

    @property
    def backend(self):
        """Return the backend."""
        return self._backend
