# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use,unused-argument,unused-variable
"""Tests for `aiida.engine.processes.workchains.restart` module."""
from aiida.backends.testbase import AiidaTestCase
from aiida.engine import ExitCode
from aiida.engine.processes.workchains.restart import validate_process_handlers
from aiida.engine.processes.workchains.utils import ProcessHandler


class TestBaseRestartWorkChain(AiidaTestCase):
    """Tests for the `BaseRestartWorkChain`."""

    def test_validate_process_handlers(self):
        """Test the `validate_process_handlers` validator."""

        def incorrect_process_handler():
            """Process handler with incorrect number of arguments."""

        def correct_process_handler(self, node):
            """Process handler with correct signature."""

        invalid_handlers = (
            ProcessHandler(incorrect_process_handler), ProcessHandler(correct_process_handler, '100'),
            ProcessHandler(correct_process_handler, 100, 200)
        )

        valid_handlers = (
            ProcessHandler(correct_process_handler), ProcessHandler(correct_process_handler, 100),
            ProcessHandler(correct_process_handler, 100, ExitCode(200))
        )

        for handler in invalid_handlers:
            assert validate_process_handlers({'key': handler}) is not None

        for handler in valid_handlers:
            assert validate_process_handlers({'key': handler}) is None
