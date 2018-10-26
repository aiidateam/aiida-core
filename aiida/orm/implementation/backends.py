# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic backend related objects"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import six

__all__ = ('Backend', 'BackendEntity', 'BackendCollection')


@six.add_metaclass(abc.ABCMeta)
class Backend(object):
    """The public interface that defines a backend factory that creates backend specific concrete objects."""

    @abc.abstractproperty
    def logs(self):
        """
        Return the collection of log entries

        :return: the log collection
        :rtype: :class:`aiida.orm.log.Log`
        """

    @abc.abstractproperty
    def users(self):
        """
        Return the collection of users

        :return: the users collection
        :rtype: :class:`aiida.orm.implementation.BackendUserCollection`
        """

    @abc.abstractproperty
    def authinfos(self):
        """
        Return the collection of authorisation information objects

        :return: the authinfo collection
        :rtype: :class:`aiida.orm.implementation.BackendAuthInfoCollection`
        """

    @abc.abstractproperty
    def computers(self):
        """
        Return the collection of computer objects

        :return: the computers collection
        :rtype: :class:`aiida.orm.implementation.BackendComputerCollection`
        """

    @abc.abstractproperty
    def query_manager(self):
        """
        Return the query manager for the objects stored in the backend

        :return: The query manger
        :rtype: :class:`aiida.backends.general.abstractqueries.AbstractQueryManager`
        """

    @abc.abstractmethod
    def query(self):
        """
        Return an instance of a query builder implementation for this backend

        :return: a new query builder instance
        :rtype: :class:`aiida.orm.implementation.BackendQueryBuilder`
        """


@six.add_metaclass(abc.ABCMeta)
class BackendEntity(object):
    """An first-class entity in the backend"""

    def __init__(self, backend):
        self._backend = backend

    @abc.abstractproperty
    def id(self):  # pylint: disable=invalid-name
        """
        Get the id for this entity.  This is unique only amongst entities of this type
        for a particular backend

        :return: the entity id
        """

    @property
    def backend(self):
        """
        Get the backend this entity belongs to

        :return: the backend instance
        """
        return self._backend

    @abc.abstractmethod
    def store(self):
        """
        Store this object.

        Whether it is possible to call store more than once is delegated to the object itself
        """
        pass

    @abc.abstractmethod
    def is_stored(self):
        """
        Is the object stored?

        :return: True if stored, False otherwise
        :rtype: bool
        """
        pass


@six.add_metaclass(abc.ABCMeta)
class BackendCollection(object):
    """Container class that represents a collection of entries of a particular backend entity."""

    ENTRY_TYPE = None

    def __init__(self, backend):
        """
        :param backend: the backend this collection belongs to
        :type backend: :class:`aiida.orm.implementation.backends.Backend`
        """
        assert self.ENTRY_TYPE is not None, "Must set the ENTRY_CLASS class variable"
        self._backend = backend

    @property
    def backend(self):
        """
        Return the backend.

        :rtype: :class:`aiida.orm.implementation.backends.Backend`
        """
        return self._backend

    @abc.abstractmethod
    def create(self, **kwargs):
        """
        Create new a entry and set the attributes to those specified in the keyword arguments

        :return: the newly created entry
        """
        pass

    def query(self):
        """
        Get a query builder instance for entries of this collection

        :return: a new query builder over the entries of this collection
        """
        query = self.backend.query()
        query.append(self.ENTRY_TYPE)
        return query
