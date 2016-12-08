# -*- coding: utf-8 -*-

from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests
from aiida.backends.tests.backup_setup_script import *


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestBackupSetupScriptUnitSQLA(SqlAlchemyTests,
                                    TestBackupSetupScriptUnit):
    pass


class TestBackupSetupScriptIntegrationSQLA(SqlAlchemyTests,
                                           TestBackupSetupScriptIntegration):
    pass
