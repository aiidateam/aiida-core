# -*- coding: utf-8 -*-
"""
Generic tests that need the be specific to sqlalchemy
"""
from aiida.backends.tests.generic import TestCode, TestComputer, TestDbExtras, TestGroups, TestWfBasic
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests


class TestComputerSqla(SqlAlchemyTests, TestComputer):
    """
    No characterization required
    """
    pass


class TestCodeSqla(SqlAlchemyTests, TestCode):
    """
     No characterization required
     """
    pass


class TestWfBasicSqla(SqlAlchemyTests, TestWfBasic):
    """
     No characterization required
     """
    pass


class TestGroupsSqla(SqlAlchemyTests, TestGroups):
    """
     No characterization required
     """
    pass


class TestDbExtrasSqla(SqlAlchemyTests, TestDbExtras):
    """
     No characterization required
     """
    pass
