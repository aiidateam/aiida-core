# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Default configuration for the REST API
"""
import os

API_CONFIG = {
    'LIMIT_DEFAULT': 400,  # default records total
    'PERPAGE_DEFAULT': 20,  # default records per page
    'PREFIX': '/api/v4',  # prefix for all URLs
    'VERSION': '4.1.0',
}

APP_CONFIG = {
    'DEBUG': False,  # use False for production
    'PROPAGATE_EXCEPTIONS': True,  # serve REST exceptions to client instead of generic 500 internal server error
}

SERIALIZER_CONFIG = {'datetime_format': 'default'}  # use 'asinput' or 'default'

CACHE_CONFIG = {'CACHE_TYPE': 'memcached'}
CACHING_TIMEOUTS = {  # Caching timeouts in seconds
    'nodes': 10,
    'users': 10,
    'calculations': 10,
    'computers': 10,
    'datas': 10,
    'groups': 10,
    'codes': 10,
}

# IO tree
MAX_TREE_DEPTH = 5

CLI_DEFAULTS = {
    'HOST_NAME': '127.0.0.1',
    'PORT': 5000,
    'CONFIG_DIR': os.path.dirname(os.path.abspath(__file__)),
    'WSGI_PROFILE': False,
    'HOOKUP_APP': True,
    'CATCH_INTERNAL_SERVER': False,
    'POSTING': True,  # Include POST endpoints (currently only /querybuilder)
}
