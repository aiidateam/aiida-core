# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.workchains.restart` module."""
from aiida.backends.testbase import AiidaTestCase
from aiida.engine.processes.workchains.restart import BaseRestartWorkChain
from aiida.engine.processes.workchains.utils import process_handler


class TestBaseRestartWorkChain(AiidaTestCase):
    """Tests for the `BaseRestartWorkChain` class."""

    @staticmethod
    def test_is_process_handler():
        """Test the `BaseRestartWorkChain.is_process_handler` class method."""

        class SomeWorkChain(BaseRestartWorkChain):
            """Dummy class."""

            @process_handler()
            def handler_a(self, node):
                pass

            def not_a_handler(self, node):
                pass

        assert SomeWorkChain.is_process_handler('handler_a')
        assert not SomeWorkChain.is_process_handler('not_a_handler')
        assert not SomeWorkChain.is_process_handler('unexisting_method')

    @staticmethod
    def test_get_process_handler():
        """Test the `BaseRestartWorkChain.get_process_handlers` class method."""

        class SomeWorkChain(BaseRestartWorkChain):
            """Dummy class."""

            @process_handler
            def handler_a(self, node):
                pass

            def not_a_handler(self, node):
                pass

        assert [handler.__name__ for handler in SomeWorkChain.get_process_handlers()] == ['handler_a']
