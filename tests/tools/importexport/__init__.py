# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for AiiDA archive files (import, export)."""
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import EXPORT_LOGGER, IMPORT_LOGGER


class AiidaArchiveTestCase(AiidaTestCase):
    """Testcase for tests of archive-related functionality (import, export)."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Only run to prepare an archive file"""
        super().setUpClass()

        # don't want output
        EXPORT_LOGGER.setLevel('CRITICAL')
        IMPORT_LOGGER.setLevel('CRITICAL')
