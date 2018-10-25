# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for backend related methods and classes"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__all__ = ['construct_backend', 'CollectionEntry']

_DJANGO_BACKEND = None
_SQLA_BACKEND = None


def construct_backend(backend_type=None):
    """
    Construct a concrete backend instance based on the backend_type or use the global backend value if not specified.

    :param backend_type: get a backend instance based on the specified type (or default)
    :return: :class:`aiida.orm.backend.Backend`
    """
    # pylint: disable=global-statement
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


class CollectionEntry(object):
    """Class that represents an entry within a collection of entries of a particular backend entity."""

    def __init__(self, backend=None):
        """
        :param backend: The backend instance
        :type backend: :class:`aiida.orm.implementation.backends.Backend`
        """
        self._backend = backend or construct_backend()

    @property
    def backend(self):
        """Return the backend."""
        return self._backend
