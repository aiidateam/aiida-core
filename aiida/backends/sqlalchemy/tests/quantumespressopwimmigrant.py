# -*- coding: utf-8 -*-
"""
Tests for the pwimmigrant plugin for Quantum Espresso specific to Django
"""

# TODO: Test exception handling of user errors.
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.orm.code import Code
from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo

#Tests imports
from aiida.backends.tests.quantumespressopwimmigrant import LocalSetup, \
    TestPwImmigrantCalculationAutomatic, TestPwImmigrantCalculationGamma, \
    TestPwImmigrantCalculationManual

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class LocalTestCase(SqlAlchemyTests, LocalSetup):
    """
    AiidaTesetCase subclass that uses local transport and defs helper methods.

    Also sets up authinfo, so calcs can be retrieved and parsed, and sets up a
    code, so test submissions can be run.
    """

    @classmethod
    def setUpClass(cls):
        super(LocalTestCase, cls).setUpClass()

        # Change transport type to local.
        cls.computer.set_transport_type('local')

        # Configure authinfo for cls.computer and cls.user.
        authinfo = DbAuthInfo(dbcomputer=cls.computer.dbcomputer,
                              aiidauser=cls.user)
        authinfo.set_auth_params({})
        authinfo.save()

        # Set up a code linked to cls.computer. The path is just a fake string.
        cls.code = Code(remote_computer_exec=(cls.computer, '/x.x')).store()

class TestPwImmigrantCalculationManualSqla(LocalTestCase,
                                        TestPwImmigrantCalculationManual):
    """
    """
    pass

class TestPwImmigrantCalculationAutomaticSqla(LocalTestCase,
                                           TestPwImmigrantCalculationAutomatic):
    """
    """
    pass


class TestPwImmigrantCalculationGammaSqla(LocalTestCase,
                                       TestPwImmigrantCalculationGamma):
    """
    """
    pass