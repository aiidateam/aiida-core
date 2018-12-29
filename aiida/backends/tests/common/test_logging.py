# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the logging module."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import logging
import unittest


class TestLogger(unittest.TestCase):
    """Test global python logging module."""

    def test_logger(self):
        """
        The python logging module is configured with a DbLogHandler
        upon runtime, but we do not want any fired log messages to
        crash when they reach the handler and no database is set yet
        """
        # pylint: disable=no-self-use
        logger = logging.getLogger('aiida')
        logger.critical('Test critical log')
