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
"""Tests for `aiida.engine.processes.workchains.utils` module."""
from aiida.backends.testbase import AiidaTestCase
from aiida.engine import ExitCode, ProcessState
from aiida.engine.processes.workchains.restart import BaseRestartWorkChain
from aiida.engine.processes.workchains.utils import register_process_handler, ProcessHandlerReport
from aiida.orm import ProcessNode
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')


class TestRegisterProcessHandler(AiidaTestCase):
    """Tests for the `register_process_handler` decorator."""

    def test_priority_keyword_only(self):
        """The `priority` should be keyword only."""
        with self.assertRaises(TypeError):

            @register_process_handler(BaseRestartWorkChain, 400)  # pylint: disable=too-many-function-args
            def _(self, node):
                pass

        @register_process_handler(BaseRestartWorkChain, priority=400)
        def _(self, node):
            pass

    def test_priority_type(self):
        """The `priority` should be an integer."""
        with self.assertRaises(TypeError):

            @register_process_handler(BaseRestartWorkChain, priority='400')
            def _(self, node):
                pass

    def test_priority(self):
        """Test that the handlers are called in order of their `priority`."""
        attribute_key = 'handlers_called'

        class ArithmeticAddBaseWorkChain(BaseRestartWorkChain):

            _process_class = ArithmeticAddCalculation

        # Register some handlers that should be called in order of 4 -> 3 -> 2 -> 1 but are on purpose registered in a
        # different order. When called, they should add their name to `handlers_called` attribute of the node. This can
        # then be checked after invoking `inspect_process` to ensure they were called in the right order
        @register_process_handler(ArithmeticAddBaseWorkChain, priority=100)
        def handler_01(self, node):
            handlers_called = node.get_attribute(attribute_key, default=[])
            handlers_called.append('handler_01')
            node.set_attribute(attribute_key, handlers_called)
            return ProcessHandlerReport(False, ExitCode(100))

        @register_process_handler(ArithmeticAddBaseWorkChain, priority=300)
        def handler_03(self, node):
            handlers_called = node.get_attribute(attribute_key, default=[])
            handlers_called.append('handler_03')
            node.set_attribute(attribute_key, handlers_called)
            return ProcessHandlerReport(False, ExitCode(300))

        @register_process_handler(ArithmeticAddBaseWorkChain, priority=200)
        def handler_02(self, node):
            handlers_called = node.get_attribute(attribute_key, default=[])
            handlers_called.append('handler_02')
            node.set_attribute(attribute_key, handlers_called)
            return ProcessHandlerReport(False, ExitCode(200))

        @register_process_handler(ArithmeticAddBaseWorkChain, priority=400)
        def handler_04(self, node):
            handlers_called = node.get_attribute(attribute_key, default=[])
            handlers_called.append('handler_04')
            node.set_attribute(attribute_key, handlers_called)
            return ProcessHandlerReport(False, ExitCode(400))

        child = ProcessNode()
        child.set_process_state(ProcessState.FINISHED)
        child.set_exit_status(400)
        process = ArithmeticAddBaseWorkChain()
        process.setup()
        process.ctx.iteration = 1
        process.ctx.children = [child]

        # Last called handler should be `handler_01` which returned `ExitCode(100)`
        assert process.inspect_process() == ExitCode(100)
        assert child.get_attribute(attribute_key, []) == ['handler_04', 'handler_03', 'handler_02', 'handler_01']

    def test_exit_codes_keyword_only(self):
        """The `exit_codes` should be keyword only."""
        with self.assertRaises(TypeError):

            @register_process_handler(BaseRestartWorkChain, ExitCode())  # pylint: disable=too-many-function-args
            def _(self, node):
                pass

        @register_process_handler(BaseRestartWorkChain, exit_codes=ExitCode())
        def _(self, node):
            pass

    def test_exit_codes_type(self):
        """The `exit_codes` should be single or list of `ExitCode` instances."""
        incorrect_types = [
            'test',
            ['test'],
            400,
            [400],
        ]

        with self.assertRaises(TypeError):
            for incorrect_type in incorrect_types:

                @register_process_handler(BaseRestartWorkChain, exit_codes=incorrect_type)
                def _(self, node):
                    pass

        @register_process_handler(BaseRestartWorkChain, exit_codes=ExitCode(400, 'Some exit code'))
        def _(self, node):
            pass

        @register_process_handler(BaseRestartWorkChain, exit_codes=[ExitCode(400, 'a'), ExitCode(401, 'b')])
        def _(self, node):
            pass

    def test_exit_codes_filter(self):
        """Test that the `exit_codes` argument properly filters, returning `None` if the `node` has different status."""

        class ArithmeticAddBaseWorkChain(BaseRestartWorkChain):

            _process_class = ArithmeticAddCalculation

        exit_code_filter = ExitCode(400)

        # This process node should match the exit code filter of the error handler
        node_match = ProcessNode()
        node_match.set_exit_status(exit_code_filter.status)

        # This one should not because it has a different exit status
        node_skip = ProcessNode()
        node_skip.set_exit_status(200)  # Some other exit status

        @register_process_handler(ArithmeticAddBaseWorkChain, exit_codes=exit_code_filter)
        def _(self, node):
            return ProcessHandlerReport()

        # Create dummy process instance
        process = ArithmeticAddBaseWorkChain()

        # Loop over all handlers, which should be just the one, and call it with the two different nodes
        for handler in process._handlers:  # pylint: disable=protected-access
            # The `node_match` should match the `exit_codes` filter and so return a report instance
            assert isinstance(handler.method(process, node_match), ProcessHandlerReport)

            # The `node_skip` has a wrong exit status and so should get skipped, returning `None`
            assert handler.method(process, node_skip) is None
