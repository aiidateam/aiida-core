# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
## Pagination defaults
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
LIMIT_DEFAULT = 400
PERPAGE_DEFAULT = 20

##Version prefix for all the URLs (in most cases, you need to omit trailing
# slash)
PREFIX="/api/v2"


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
cache_config={'CACHE_TYPE': 'memcached'}
CACHING_TIMEOUTS = { #Caching TIMEOUTS (in seconds)
    'nodes': 10,
    'users': 10,
    'calculations': 10,
    'computers': 10,
    'datas': 10,
    'groups': 10,
    'codes': 10,
}

"""
Schema customization (if file schema_custom.json is present in this same folder)
"""
#TODO add more verbose description
import os
import ujson as uj

schema_custom_config = os.path.join(os.path.split(__file__)[0], 'schema_custom.json')
try:
    with open(schema_custom_config) as fin:
        custom_schema = uj.load(fin)
except IOError:
    custom_schema = {}

# IO tree
MAX_TREE_DEPTH = 5

"""
Aiida profile used by the REST api when no profile is specified (ex. by
--aiida-profile flag).
This has to be one of the profiles registered in .aiida/config.json

In case you want to use the default stored in
.aiida/config.json, set this varibale to "default"

"""
default_aiida_profile = 'sqlalchemy'