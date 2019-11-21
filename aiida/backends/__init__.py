# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for implementations of database backends."""

BACKEND_DJANGO = 'django'
BACKEND_SQLA = 'sqlalchemy'


def get_backend_manager(backend):
    """Get an instance of the `BackendManager` for the current backend.

    :param backend: the type of the database backend
    :return: `BackendManager`
    """
    if backend == BACKEND_DJANGO:
        from aiida.backends.djsite.manager import DjangoBackendManager
        return DjangoBackendManager()

    if backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.manager import SqlaBackendManager
        return SqlaBackendManager()

    raise Exception('unknown backend type `{}`'.format(backend))
