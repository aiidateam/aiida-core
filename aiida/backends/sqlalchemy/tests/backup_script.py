# -*- coding: utf-8 -*-

from aiida.backends.tests.backup_script import *
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.common.additions.backup_script.backup_sqlalchemy import Backup

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestBackupScriptUnitSQLA(SqlAlchemyTests, TestBackupScriptUnit):
    def setUp(self):
        super(SqlAlchemyTests, self).setUp()
        if not is_dbenv_loaded():
            load_dbenv()

        self._backup_setup_inst = Backup("", 2)

    def tearDown(self):
        self._backup_setup_inst = None


class TestBackupScriptIntegrationSQLA(SqlAlchemyTests,
                                      TestBackupScriptIntegration):
    pass
