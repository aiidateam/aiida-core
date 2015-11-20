# -*- coding: utf-8 -*-

import unittest

from aiida.backends.sqlalchemy.utils import load_profile

PROFILE = "tests"


if __name__ == "__main__":
    load_profile(profile=PROFILE)
    from aiida.backends.sqlalchemy.tests.nodes import *
    from aiida.backends.sqlalchemy.tests.dataclasses import *
    unittest.main()
