# -*- coding: utf-8 -*-
"""
Tests for the pw input plugin specific to sqlalchemy
"""

from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.quantumespressopw import TestQEPWInputGeneration
from aiida.orm.code import Code

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For " \
                u"further information please visit http://www.aiida.net/. All " \
                u"rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestQEPWInputGenerationSqla(SqlAlchemyTests, TestQEPWInputGeneration):
    """
    tests that are specific to Django
    """

    #The setupClass is overwritten to add specific objects
    @classmethod
    def setUpClass(cls):
        super(TestQEPWInputGenerationSqla, cls).setUpClass()

        cls.calc_params = {
            'computer': cls.computer,
            'resources': {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }
        }

        cls.code = Code()
        cls.code.set_remote_computer_exec((cls.computer, '/x.x'))
        cls.code.store()


    pass

