# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"

AIIDADB_PROFILE = None
CURRENT_AIIDADB_PROCESS = None
LOAD_DBENV_CALLED = False # Set to True at the first call of load_dbenv

# CUSTOM USER CLASS
AUTH_USER_MODEL = 'db.DbUser'
# VERSION TO USE FOR DBNODES.
AIIDANODES_UUID_VERSION = 4
