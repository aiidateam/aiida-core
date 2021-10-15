# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Backend-agnostic utility functions"""
from aiida.backends import BACKEND_DJANGO, BACKEND_SQLA
from aiida.manage import configuration

AIIDA_ATTRIBUTE_SEP = '.'


def delete_nodes_and_connections(pks):
    """Backend-agnostic function to delete Nodes and connections"""
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import delete_nodes_and_connections_django as delete_nodes_backend
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import delete_nodes_and_connections_sqla as delete_nodes_backend
    else:
        raise Exception(f'unknown backend {configuration.PROFILE.database_backend}')

    delete_nodes_backend(pks)
