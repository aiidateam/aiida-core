# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



raw_session = None

def _generate_thread_safe_session():
    from sqlalchemy.orm import scoped_session

    if raw_session is None:
        return None
    else:
        ScopedSession  = scoped_session(raw_session)
        return ScopedSession()

session = property(_generate_thread_safe_session)

