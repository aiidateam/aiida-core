# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

# This variable identifies the schema version of this file.
# Every time you change the schema below in *ANY* way, REMEMBER TO CHANGE
# the version here in the migration file and update migrations/__init__.py.
# See the documentation for how to do all this.
#
# The version is checked at code load time to verify that the code schema
# version and the DB schema version are the same. (The DB schema version
# is stored in the DbSetting table and the check is done in the
# load_dbenv() function).
SCHEMA_VERSION = 0.1
