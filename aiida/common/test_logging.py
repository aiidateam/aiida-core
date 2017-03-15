# -*- coding: utf-8 -*-
import logging
import unittest

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1"
__authors__ = "The AiiDA team."


class TestLogger(unittest.TestCase):
    """
    Test global python logging module
    """

    def test_logger(self):
        """
        The python logging module is configured with a DbLogHandler
        upon runtime, but we do not want any fired log messages to
        crash when they reach the handler and no database is set yet
        """
        logger = logging.getLogger('aiida')
        logger.critical('Test critical log')