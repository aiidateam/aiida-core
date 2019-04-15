# -*- coding: utf-8 -*-

import unittest

from aiida.backends.sqlalchemy.utils import load_profile

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

PROFILE = "tests"


if __name__ == "__main__":
    load_profile(profile=PROFILE)
    from aiida.backends.sqlalchemy.tests.nodes import *
    from aiida.backends.sqlalchemy.tests.dataclasses import *
    from aiida.backends.sqlalchemy.tests.generic import *
    unittest.main()
