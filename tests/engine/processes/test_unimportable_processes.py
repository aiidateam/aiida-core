###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Run processes the daemon cannot import, end to end through a real worker.

A daemon worker imports from the ``sys.path`` the daemon froze when it started. These tests put code where that
path does not reach, which is what a Jupyter notebook and a scratch directory both amount to, and check that the
worker runs it anyway.

The unit tests elsewhere pin each decision on its own. These pin that the decisions add up to a process that runs.
"""

import time
from collections.abc import Callable
from types import ModuleType

import pytest

from aiida import orm
from aiida.common import callables
from aiida.engine import WorkChain, calcfunction
from aiida.engine.daemon.client import DaemonClient
from aiida.engine.processes import _class_identity
from aiida.orm import InstalledCode, ProcessNode

pytestmark = [pytest.mark.requires_broker, pytest.mark.usefixtures('started_daemon_client')]


def identity_of(cls):
    """Return what a checkpoint would record for ``cls``, to pin a test's precondition."""
    from aiida.common import loaders

    return _class_identity.identity_policy.recorded_for(value=cls, loader=loaders.get_object_loader())


@pytest.fixture
def unreachable_module(started_daemon_client: DaemonClient, importable_module: Callable[..., ModuleType]):
    """A module this interpreter can import and the running daemon cannot.

    The daemon is started by the fixture this depends on, so it has already frozen its ``sys.path`` by the time the
    directory is created, let alone added.
    """
    module = importable_module(
        'unreachable_workflows',
        """
        import unreachable_helper
        from aiida import orm
        from aiida.engine import WorkChain


        class UnreachableWorkChain(WorkChain):
            \"\"\"Importable here and nowhere the daemon can see.\"\"\"

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('text', valid_type=orm.Str)
                spec.outline(cls.compute)
                spec.output('shouted', valid_type=orm.Str)

            def compute(self):
                self.out('shouted', orm.Str(unreachable_helper.shout(self.inputs.text.value)).store())
        """,
        unreachable_helper='def shout(text):\n    return text.upper()\n',
    )

    assert not callables.module_resolves_in('unreachable_workflows', _class_identity.get_daemon_import_paths()), (
        'the daemon can import the module, so this test would prove nothing'
    )

    return module


class NotebookWorkChain(WorkChain):
    """Stands in for a class defined in a notebook cell, once ``unresolvable_in_main`` has relabelled it."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int)
        spec.outline(cls.compute)
        spec.output('total', valid_type=orm.Int)

    def compute(self):
        self.out('total', orm.Int(self.inputs.x.value + 1).store())


@calcfunction
def notebook_add(x):
    """Stands in for a process function defined in a notebook cell."""
    return x + 1


def test_workchain_from_a_module_the_daemon_cannot_import(
    submit_and_await: Callable[..., ProcessNode], unreachable_module: ModuleType
):
    node = submit_and_await(unreachable_module.UnreachableWorkChain, text=orm.Str('quiet'))

    assert node.is_finished_ok, node.exception
    assert node.outputs.shouted.value == 'QUIET'


def test_workchain_defined_in_main(submit_and_await: Callable[..., ProcessNode], unresolvable_in_main):
    node = submit_and_await(unresolvable_in_main(NotebookWorkChain), x=orm.Int(41))

    assert node.is_finished_ok, node.exception
    assert node.outputs.total.value == 42


def test_process_function_defined_in_main(
    submit_and_await: Callable[..., ProcessNode], monkeypatch: pytest.MonkeyPatch
):
    """A process function is identified by the function rather than by the class built for it, so the function is
    what has to reach the worker.
    """
    from aiida.engine import submit

    monkeypatch.setattr(notebook_add, '__module__', '__main__')
    monkeypatch.setattr(notebook_add.process_class, '__module__', '__main__')

    assert identity_of(notebook_add.process_class).class_bytes is not None, (
        'the daemon can resolve this function, so this test would prove nothing'
    )

    node = submit_and_await(submit(notebook_add, x=orm.Int(41)))

    assert node.is_finished_ok, node.exception
    assert node.outputs.result.value == 42


def test_an_installed_plugin_still_travels_by_name(
    submit_and_await: Callable[..., ProcessNode], aiida_code_installed: Callable[..., InstalledCode]
):
    """Test that a registered plugin carries no process class bytes, which keeps an ordinary checkpoint small."""
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    assert identity_of(ArithmeticAddCalculation).class_bytes is None

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = orm.Int(2)
    builder.y = orm.Int(40)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.sum.value == 42
    assert node.process_type == 'aiida.calculations:core.arithmetic.add'


def test_calcjob_defined_in_main(
    submit_and_await: Callable[..., ProcessNode],
    unresolvable_in_main,
    aiida_code_installed: Callable[..., InstalledCode],
):
    """Carrying the class is not enough on its own here: the parser reads the output spec from the process class, and
    takes it from the running process rather than the node, which carries only the name it was recorded under.
    """
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    class MainCalcJob(ArithmeticAddCalculation):
        """Stands in for a calculation job defined in a notebook cell."""

        @classmethod
        def define(cls, spec):
            super().define(spec)

    unresolvable_in_main(MainCalcJob)

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = MainCalcJob.get_builder()
    builder.code = code
    builder.x = orm.Int(2)
    builder.y = orm.Int(40)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.sum.value == 42

    # The record of what ran outlives the checkpoint that carried it. The source is read from the file the
    # class's own methods were compiled from, since `__main__` has none to offer.
    #
    # Sealing is what deletes the checkpoint, and it lands just after the state that `submit_and_await` waits for.
    for _ in range(100):
        node = orm.load_node(node.pk)
        if node.is_sealed:
            break
        time.sleep(0.1)

    assert node.is_sealed
    assert node.checkpoint is None
