# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Constants used in rest api
"""

## Pagination defaults
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
LIMIT_DEFAULT = 400
PERPAGE_DEFAULT = 20

##Version prefix for all the URLs
PREFIX = "/api/v2"
"""
Flask app configs.

DEBUG: True/False. enables debug mode N.B.
!!!For production run use ALWAYS False!!!

PROPAGATE_EXCEPTIONS: True/False serve REST exceptions to the client (and not a
generic 500: Internal Server Error exception)

"""
APP_CONFIG = {
    'DEBUG': False,
    'PROPAGATE_EXCEPTIONS': True,
}
"""
JSON serialization config. Leave this dictionary empty if default Flask
serializer is desired.

Here is a list a all supported fields. If a field is not present in the
dictionary its value is assumed to be 'default'.

DATETIME_FORMAT: allowed values are 'asinput' and 'default'.

"""
SERIALIZER_CONFIG = {'datetime_format': 'default'}
"""
Caching configuration

memcached: backend caching system
"""
CACHE_CONFIG = {'CACHE_TYPE': 'memcached'}
CACHING_TIMEOUTS = { #Caching TIMEOUTS (in seconds)
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
"""
Aiida profile used by the REST api when no profile is specified (ex. by
--aiida-profile flag).
This has to be one of the profiles registered in .aiida/config.json

In case you want to use the default stored in
.aiida/config.json, set this varibale to "default"

"""
DEFAULT_AIIDA_PROFILE = None
