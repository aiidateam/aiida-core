# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import 
import click


def command():
    """
    Wrapped decorator for click's command decorator, which makes sure
    that the database environment is loaded
    """
    from aiida.cmdline.utils.decorators import with_dbenv

    @click.command
    @with_dbenv()
    def inner():
        func(*args, **kwargs)

    return inner
