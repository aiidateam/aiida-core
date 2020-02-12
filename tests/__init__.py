# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for defining tests that required access to (a temporary) database."""
from aiida import __version__ as version_core

# The following statement needs to be here for the tests in `tests.plugins.test_utils.py` to work. There, some processes
# are defined in place, such as a `WorkChain` and a calcfunction and the version of their "plugin" is defined as the
# version of the top-level module in which they are defined, which is this `tests` module.
__version__ = version_core
