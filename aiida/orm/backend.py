# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from abc import abstractproperty, ABCMeta

_DJANGO_BACKEND = None
_SQLA_BACKEND   = None

def construct(backend_type=None):
    """
    Construct a concrete backend instance based on the backend_type
    or use the global backend value if not specified.

    :param backend_type: Get a backend instance based on the specified
        type (or default)
    :return: :class:`Backend`
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


class Backend(object):
    """
    The public interface that defines a backend factory that creates backend
    specific concrete objects.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def log(self):
        """
        Get an object that implements the logging utilities interface.

        :return: An concrete log utils object
        :rtype: :class:`aiida.orm.log.Log`
        """
        pass