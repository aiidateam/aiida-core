###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `aiida.engine.processes.workchains.restart` module."""

import warnings

import pytest

from aiida import engine, orm
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

    @engine.process_handler(priority=0, enabled=False)
    def handler_c(self, _):
        return

    def not_a_handler(self, _):
        pass


def test_is_process_handler():
    """Test the `BaseRestartWorkChain.is_process_handler` class method."""
    assert SomeWorkChain.is_process_handler('handler_a')
    assert not SomeWorkChain.is_process_handler('not_a_handler')
    assert not SomeWorkChain.is_process_handler('unexisting_method')


def test_get_process_handlers():
    """Test the `BaseRestartWorkChain.get_process_handlers` class method."""
    assert [handler.__name__ for handler in SomeWorkChain.get_process_handlers()] == [
        'handler_a',
        'handler_b',
        'handler_c',
    ]


@pytest.mark.parametrize(
    'inputs, priorities',
    (
        ({}, [100, 200]),
        ({'handler_overrides': {'handler_c': {'enabled': True}}}, [0, 100, 200]),
        ({'handler_overrides': {'handler_a': {'priority': 50}}}, [50, 100]),
        ({'handler_overrides': {'handler_a': {'enabled': False}}}, [100]),
        ({'handler_overrides': {'handler_a': False}}, [100]),  # This notation is deprecated
    ),
)
def test_get_process_handlers_by_priority(generate_work_chain, inputs, priorities):
    """Test the `BaseRestartWorkChain.get_process_handlers_by_priority` method."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        process = generate_work_chain(SomeWorkChain, inputs)
    process.setup()
    handlers = process.get_process_handlers_by_priority()
    assert sorted([priority for priority, _ in handlers]) == priorities

    # Verify the actual handlers on the class haven't been modified
    assert getattr(SomeWorkChain, 'handler_a').priority == 200
    assert getattr(SomeWorkChain, 'handler_b').priority == 100
    assert getattr(SomeWorkChain, 'handler_c').priority == 0
    assert getattr(SomeWorkChain, 'handler_a').enabled
    assert getattr(SomeWorkChain, 'handler_b').enabled
    assert not getattr(SomeWorkChain, 'handler_c').enabled

    # Validate that a second invocation return the exact same results. This is a regression test for
    # https://github.com/aiidateam/aiida-core/issues/6307. Note that the handlers are compared by name, because the
    # bound methods will be separate clones and the ``__eq__`` operation will return ``False`` even though it represents
    # the same handler function.
    assert [(p, h.__name__) for p, h in process.get_process_handlers_by_priority()] == [
        (p, h.__name__) for p, h in handlers
    ]


@pytest.mark.requires_rmq
def test_excepted_process(generate_work_chain, generate_calculation_node):
    """Test that the workchain aborts if the sub process was excepted."""
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(engine.ProcessState.EXCEPTED)]
    assert process.inspect_process() == engine.BaseRestartWorkChain.exit_codes.ERROR_SUB_PROCESS_EXCEPTED


@pytest.mark.requires_rmq
def test_killed_process(generate_work_chain, generate_calculation_node):
    """Test that the workchain aborts if the sub process was killed."""
    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    process.ctx.children = [generate_calculation_node(engine.ProcessState.KILLED)]
    assert process.inspect_process() == engine.BaseRestartWorkChain.exit_codes.ERROR_SUB_PROCESS_KILLED


@pytest.mark.requires_rmq
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
    assert (
        process.inspect_process() == engine.BaseRestartWorkChain.exit_codes.ERROR_SECOND_CONSECUTIVE_UNHANDLED_FAILURE
    )


@pytest.mark.requires_rmq
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


@pytest.mark.requires_rmq
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


@pytest.mark.requires_rmq
def test_run_process(generate_work_chain, generate_calculation_node, monkeypatch):
    """Test the `run_process` method."""

    def mock_submit(_, process_class, **kwargs):
        """Mock the submission to just return an empty `CalcJobNode`."""
        assert process_class is SomeWorkChain._process_class
        assert 'metadata' in kwargs
        assert kwargs['metadata']['call_link_label'] == 'iteration_01'
        return generate_calculation_node()

    monkeypatch.setattr(SomeWorkChain, 'submit', mock_submit)

    process = generate_work_chain(SomeWorkChain, {})
    process.setup()
    result = process.run_process()

    assert isinstance(result, engine.ToContext)
    assert isinstance(result['children'], Awaitable)
    assert process.node.base.extras.get(SomeWorkChain._considered_handlers_extra) == [[]]


class OutputNamespaceWorkChain(engine.WorkChain):
    """A WorkChain has namespaced output"""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('parameters', required=False, valid_type=orm.Dict)
        spec.output_namespace('sub', valid_type=orm.Int, dynamic=True)
        spec.outline(cls.finalize)

    def finalize(self):
        self.out('sub.result', orm.Int(1).store())


class CustomBaseRestartWorkChain(engine.BaseRestartWorkChain):
    """`BaseRestartWorkChain` of `OutputNamespaceWorkChain`"""

    _process_class = OutputNamespaceWorkChain

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(cls._process_class, namespace='sub')
        spec.expose_outputs(cls._process_class)
        spec.output('extra', valid_type=orm.Int)

        spec.outline(
            cls.setup,
            engine.while_(cls.should_run_process)(
                cls.run_process,
                cls.inspect_process,
            ),
            cls.results,
        )

    def setup(self):
        """Unwrap the ``parameters`` input if specified.

        This serves to test that the ``BaseRestartWorkChain._wrap_bare_dict_inputs`` method works properly.
        """
        super().setup()
        self.ctx.inputs = self.exposed_inputs(self._process_class, namespace='sub')
        if 'parameters' in self.ctx.inputs:
            self.ctx.inputs.parameters = self.ctx.inputs.parameters.get_dict()


@pytest.mark.requires_rmq
def test_results():
    results, node = engine.launch.run_get_node(CustomBaseRestartWorkChain)
    assert results['sub'].result.value == 1
    assert node.exit_status == 11


@pytest.mark.requires_rmq
def test_wrap_bare_dict_inputs():
    """Test that ``BaseRestartWorkChain._wrap_bare_dict_inputs`` method works properly.

    This is called in ``BaseRestartWorkChain.run_process`` which will automatically wrap any inputs that are plain
    dictionaries that should be ``Dict`` nodes. This is useful if the implementation unwraps ``Dict`` inputs in the
    preparation phase so they can be updated if needed, and they don't have to manually rewrap in a ``Dict`` node.
    """
    _, node = engine.launch.run_get_node(CustomBaseRestartWorkChain, **{'sub': {'parameters': orm.Dict({'a': 1})}})
    assert node.is_finished
