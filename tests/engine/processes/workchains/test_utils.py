###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.workchains.utils` module."""

import pytest

from aiida.engine import ExitCode, ProcessState
from aiida.engine.processes.workchains.restart import BaseRestartWorkChain
from aiida.engine.processes.workchains.utils import ProcessHandlerReport, process_handler
from aiida.orm import ProcessNode
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


@pytest.mark.requires_rmq
class TestRegisterProcessHandler:
    """Tests for the `process_handler` decorator."""

    def test_priority_keyword_only(self):
        """The `priority` should be keyword only."""
        with pytest.raises(TypeError):

            class SomeWorkChain(BaseRestartWorkChain):
                @process_handler(400)
                def _(self, node):
                    pass

        class SomeWorkChain(BaseRestartWorkChain):
            @process_handler(priority=400)
            def _(self, node):
                pass

    def test_priority_type(self):
        """The `priority` should be an integer."""
        with pytest.raises(TypeError):

            class SomeWorkChain(BaseRestartWorkChain):
                @process_handler(priority='400')
                def _(self, node):
                    pass

    def test_priority(self):
        """Test that the handlers are called in order of their `priority`."""
        attribute_key = 'handlers_called'

        class ArithmeticAddBaseWorkChain(BaseRestartWorkChain):
            """Implementation of a possible BaseRestartWorkChain for the ``ArithmeticAddCalculation``."""

            _process_class = ArithmeticAddCalculation

            # Register some handlers that should be called in order of 4 -> 3 -> 2 -> 1 but are on purpose registered in
            # a different order. When called, they should add their name to `handlers_called` attribute of the node.
            # This can then be checked after invoking `inspect_process` to ensure they were called in the right order
            @process_handler(priority=100)
            def handler_01(self, node):
                """Example handler returing ExitCode 100."""
                handlers_called = node.base.attributes.get(attribute_key, default=[])
                handlers_called.append('handler_01')
                node.base.attributes.set(attribute_key, handlers_called)
                return ProcessHandlerReport(False, ExitCode(100))

            @process_handler(priority=300)
            def handler_03(self, node):
                """Example handler returing ExitCode 300."""
                handlers_called = node.base.attributes.get(attribute_key, default=[])
                handlers_called.append('handler_03')
                node.base.attributes.set(attribute_key, handlers_called)
                return ProcessHandlerReport(False, ExitCode(300))

            @process_handler(priority=200)
            def handler_02(self, node):
                """Example handler returing ExitCode 200."""
                handlers_called = node.base.attributes.get(attribute_key, default=[])
                handlers_called.append('handler_02')
                node.base.attributes.set(attribute_key, handlers_called)
                return ProcessHandlerReport(False, ExitCode(200))

            @process_handler(priority=400)
            def handler_04(self, node):
                """Example handler returing ExitCode 400."""
                handlers_called = node.base.attributes.get(attribute_key, default=[])
                handlers_called.append('handler_04')
                node.base.attributes.set(attribute_key, handlers_called)
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
        assert child.base.attributes.get(attribute_key, []) == ['handler_04', 'handler_03', 'handler_02', 'handler_01']

    def test_exit_codes_keyword_only(self):
        """The `exit_codes` should be keyword only."""
        with pytest.raises(TypeError):

            class SomeWorkChain(BaseRestartWorkChain):
                @process_handler(ExitCode())
                def _(self, node):
                    pass

        class SomeWorkChain(BaseRestartWorkChain):
            @process_handler(exit_codes=ExitCode())
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

        with pytest.raises(TypeError):
            for incorrect_type in incorrect_types:

                class SomeWorkChain(BaseRestartWorkChain):
                    @process_handler(exit_codes=incorrect_type)
                    def _(self, node):
                        pass

        class SomeWorkChain(BaseRestartWorkChain):
            @process_handler(exit_codes=ExitCode(400, 'Some exit code'))
            def _(self, node):
                pass

        class SomeWorkChain(BaseRestartWorkChain):  # noqa: F811
            @process_handler(exit_codes=[ExitCode(400, 'a'), ExitCode(401, 'b')])
            def _(self, node):
                pass

    def test_exit_codes_filter(self):
        """Test that the `exit_codes` argument properly filters, returning `None` if the `node` has different status."""
        exit_code_filter = ExitCode(400)

        # This process node should match the exit code filter of the error handler
        node_match = ProcessNode()
        node_match.set_exit_status(exit_code_filter.status)

        # This one should not because it has a different exit status
        node_skip = ProcessNode()
        node_skip.set_exit_status(200)  # Some other exit status

        class ArithmeticAddBaseWorkChain(BaseRestartWorkChain):
            """Minimal base restart workchain for the ``ArithmeticAddCalculation``."""

            _process_class = ArithmeticAddCalculation

            @process_handler(exit_codes=exit_code_filter)
            def _(self, node):
                return ProcessHandlerReport()

        # Create dummy process instance
        process = ArithmeticAddBaseWorkChain()

        # Loop over all handlers, which should be just the one, and call it with the two different nodes
        for handler in process.get_process_handlers():
            # The `node_match` should match the `exit_codes` filter and so return a report instance
            assert isinstance(handler(process, node_match), ProcessHandlerReport)

            # The `node_skip` has a wrong exit status and so should get skipped, returning `None`
            assert handler(process, node_skip) is None

    def test_enabled_keyword_only(self):
        """The `enabled` should be keyword only."""
        with pytest.raises(TypeError):

            class SomeWorkChain(BaseRestartWorkChain):
                @process_handler(True)
                def _(self, node):
                    pass

        class SomeWorkChain(BaseRestartWorkChain):
            @process_handler(enabled=False)
            def _(self, node):
                pass

    def test_enabled(self):
        """The `enabled` should be keyword only."""

        class SomeWorkChain(BaseRestartWorkChain):
            @process_handler
            def enabled_handler(self, node):
                pass

        assert SomeWorkChain.enabled_handler.enabled

        class SomeWorkChain(BaseRestartWorkChain):
            @process_handler(enabled=False)
            def disabled_handler(self, node):
                pass

        assert not SomeWorkChain.disabled_handler.enabled

    def test_empty_exit_codes_list(self):
        """A `process_handler` with an empty `exit_codes` list should not run."""

        class SomeWorkChain(BaseRestartWorkChain):
            _process_class = ArithmeticAddCalculation

            @process_handler(exit_codes=[])
            def should_not_run(self, node):
                raise ValueError('This should not run.')

        child = ProcessNode()
        child.set_process_state(ProcessState.FINISHED)

        process = SomeWorkChain()
        process.setup()
        process.ctx.iteration = 1
        process.ctx.children = [child]
        process.inspect_process()
