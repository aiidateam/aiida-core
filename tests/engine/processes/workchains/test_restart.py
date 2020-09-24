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
# pylint: disable=invalid-name,no-self-use,no-member
import pytest

from aiida import engine
from aiida.engine.processes.workchains.awaitable import Awaitable


class SomeWorkChain(engine.BaseRestartWorkChain):
    """Dummy class."""

    _process_class = engine.CalcJob

    def setup(self):
        super().setup()
        self.ctx.inputs = {}

    @engine.process_handler(priority=200)
    def handler_a(self, node):
        if node.exit_status == 400:
            return engine.ProcessHandlerReport(do_break=False, exit_code=engine.ExitCode(418, 'IMATEAPOT'))

    @engine.process_handler(priority=100)
    def handler_b(self, _):
        return

    def not_a_handler(self, _):
        pass


def test_is_process_handler():
    """Test the `BaseRestartWorkChain.is_process_handler` class method."""
    assert SomeWorkChain.is_process_handler('handler_a')
    assert not SomeWorkChain.is_process_handler('not_a_handler')
    assert not SomeWorkChain.is_process_handler('unexisting_method')


def test_get_process_handler():
    """Test the `BaseRestartWorkChain.get_process_handlers` class method."""
    assert [handler.__name__ for handler in SomeWorkChain.get_process_handlers()] == ['handler_a', 'handler_b']


@pytest.mark.usefixtures('clear_database_before_test')
def test_excepted_process(generate_work_chain, generate_calculation_node):
    """Test that the workchain aborts if the sub process was excepted."""
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(engine.ProcessState.EXCEPTED)]
    assert process.inspect_process() == engine.BaseRestartWorkChain.exit_codes.ERROR_SUB_PROCESS_EXCEPTED


@pytest.mark.usefixtures('clear_database_before_test')
def test_killed_process(generate_work_chain, generate_calculation_node):
    """Test that the workchain aborts if the sub process was killed."""
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(engine.ProcessState.KILLED)]
    assert process.inspect_process() == engine.BaseRestartWorkChain.exit_codes.ERROR_SUB_PROCESS_KILLED


@pytest.mark.usefixtures('clear_database_before_test')
def test_unhandled_failure(generate_work_chain, generate_calculation_node):
    """Test the unhandled failure mechanism.

    The workchain should be aborted if there are two consecutive failed sub processes that went unhandled. We simulate
    it by setting `ctx.unhandled_failure` to True and append two failed process nodes in `ctx.children`.
    """
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(exit_status=100)]
    assert process.inspect_process() is None
    assert process.ctx.unhandled_failure is True

    process.ctx.children.append(generate_calculation_node(exit_status=100))
    assert process.inspect_process(
    ) == engine.BaseRestartWorkChain.exit_codes.ERROR_SECOND_CONSECUTIVE_UNHANDLED_FAILURE  # pylint: disable=no-member


@pytest.mark.usefixtures('clear_database_before_test')
def test_unhandled_reset_after_success(generate_work_chain, generate_calculation_node):
    """Test `ctx.unhandled_failure` is reset to `False` in `inspect_process` after a successful process."""
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(exit_status=100)]
    assert process.inspect_process() is None
    assert process.ctx.unhandled_failure is True

    process.ctx.children.append(generate_calculation_node(exit_status=0))
    assert process.inspect_process() is None
    assert process.ctx.unhandled_failure is False


@pytest.mark.usefixtures('clear_database_before_test')
def test_unhandled_reset_after_handled(generate_work_chain, generate_calculation_node):
    """Test `ctx.unhandled_failure` is reset to `False` in `inspect_process` after a handled failed process."""
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(exit_status=300)]
    assert process.inspect_process() is None
    assert process.ctx.unhandled_failure is True

    # Exit status 400 of the last calculation job will be handled and so should reset the flag
    process.ctx.children.append(generate_calculation_node(exit_status=400))
    result = process.inspect_process()

    # Even though `handler_a` was followed by `handler_b`, we should retrieve the exit_code from `handler_a` because
    # `handler_b` returned `None` which should not overwrite the last report.
    assert isinstance(result, engine.ExitCode)
    assert result.status == 418
    assert result.message == 'IMATEAPOT'
    assert process.ctx.unhandled_failure is False


@pytest.mark.usefixtures('clear_database_before_test')
def test_run_process(generate_work_chain, generate_calculation_node, monkeypatch):
    """Test the `run_process` method."""

    def mock_submit(_, process_class, **kwargs):
        """Mock the submission to just return an empty `CalcJobNode`."""
        assert process_class is SomeWorkChain._process_class  # pylint: disable=protected-access
        assert 'metadata' in kwargs
        assert kwargs['metadata']['call_link_label'] == 'iteration_01'
        return generate_calculation_node()

    monkeypatch.setattr(SomeWorkChain, 'submit', mock_submit)

    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    result = process.run_process()

    assert isinstance(result, engine.ToContext)
    assert isinstance(result['children'], Awaitable)
    assert process.node.get_extra(SomeWorkChain._considered_handlers_extra) == [[]]  # pylint: disable=protected-access
