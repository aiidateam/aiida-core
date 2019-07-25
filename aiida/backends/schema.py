# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for settings and utilities to determine and set the database schema versions."""
from __future__ import absolute_import
from distutils.version import StrictVersion

from aiida.common import exceptions
from .utils import get_settings_manager

SCHEMA_GENERATION_KEY = 'schema_generation'  # The key  to store the database schema generation in the settings table
SCHEMA_GENERATION_VALUE = '2'  # The current schema generation
SCHEMA_VERSION_RESET = '1.0.42'  # The schema version required to perform a migration generation reset


def get_schema_generation():
    """Return the database schema generation stored."""
    manager = get_settings_manager()

    try:
        setting = manager.get(SCHEMA_GENERATION_KEY)
        return StrictVersion(setting.value)
    except exceptions.NotExistent:
        return StrictVersion('1')


def update_schema_generation():
    """Update the schema generation to the current value."""
    manager = get_settings_manager()
    manager.set(SCHEMA_GENERATION_KEY, SCHEMA_GENERATION_VALUE)
