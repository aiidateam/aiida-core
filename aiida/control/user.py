# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Create, configure, manage users"""


def get_or_new_user(**kwargs):
    """find an existing user or instantiate a new one (unstored)"""
    from aiida.orm import User
    candidates = User.search_for_users(**kwargs)
    if candidates:
        user = candidates[0]
        created = False
    else:
        user = User(**kwargs)
        created = True
    return user, created
