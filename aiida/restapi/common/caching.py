# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from flask_cache import Cache
from aiida.restapi.api import app
from aiida.restapi.common.config import cache_config

#Would be nice to be able to specify here what has to be cached or not!
#Probably this is not doable because cachced and memoize only work as decorators
cache = Cache(app, config=cache_config)
