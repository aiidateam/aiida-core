# -*- coding: utf-8 -*-

from aiida.backends.tests.backup_script import *
from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.common.additions.backup_script.backup_django import Backup

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestBackupScriptUnitDjango(AiidaTestCase, TestBackupScriptUnit):
    def setUp(self):
        super(AiidaTestCase, self).setUp()
        if not is_dbenv_loaded():
            load_dbenv()

        self._backup_setup_inst = Backup("", 2)

    def tearDown(self):
        self._backup_setup_inst = None


class TestBackupScriptIntegrationDjango(AiidaTestCase,
                                        TestBackupScriptIntegration):
    pass
