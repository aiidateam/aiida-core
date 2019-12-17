# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for implementations of database backends.

.. deprecated:: 1.0.0
    Will be removed in `v1.1.0`, use :mod:`aiida.backends` instead.
"""

import warnings

from aiida.common.warnings import AiidaDeprecationWarning

warnings.warn('this module is deprecated', AiidaDeprecationWarning)  # pylint: disable=no-member

# Possible choices for backend
BACKEND_DJANGO = 'django'
BACKEND_SQLA = 'sqlalchemy'

# These appearingly random attributes *need* to be here, otherwise the building of the docs will fail on python 3.
# This problem appeared after the mechanism for loading profiles and the database backend was changed significantly.
# Since then Sphinx started failing with an exception that the attributes `run` and `runctx` are not defined in the
# `profile` module. What it should be targeting is the `cProfile` method, but somehow it ends up here. Simply adding
# the attributes here fixes the problem, even though we have absolutely no idea why. Given that the module is deprecated
# anyway and will soon be removed at which point the problem should no longer exist.
run = None  # pylint: disable=invalid-name
runctx = None  # pylint: disable=invalid-name
