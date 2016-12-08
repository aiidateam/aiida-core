# -*- coding: utf-8 -*-

import json
import shutil
import tempfile
import os

from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.backup_setup_script import *


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestBackupSetupScriptUnitDjango(AiidaTestCase,
                                      TestBackupSetupScriptUnit):
    pass


class TestBackupSetupScriptIntegration(AiidaTestCase,
                                       TestBackupSetupScriptIntegration):
    pass
