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

import sys
import textwrap
import time

import pytest

from aiida import orm
from aiida.common import callables
from aiida.engine import WorkChain, calcfunction
from aiida.engine.processes import persistence

pytestmark = [pytest.mark.requires_broker, pytest.mark.usefixtures('started_daemon_client')]


@pytest.fixture
def unreachable_module(started_daemon_client, tmp_path):
    """Yield a module this interpreter can import and the running daemon cannot.

    The daemon is started by the fixture this depends on, so it has already frozen its ``sys.path`` by the time the
    directory is created, let alone added.
    """
    (tmp_path / 'unreachable_helper.py').write_text('def shout(text):\n    return text.upper()\n')
    (tmp_path / 'unreachable_workflows.py').write_text(
        textwrap.dedent("""
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
            """)
    )
    sys.path.insert(0, str(tmp_path))

    try:
        import unreachable_workflows

        assert not callables.module_resolves_in('unreachable_workflows', persistence.reader_import_paths()), (
            'the daemon can import the module, so this test would prove nothing'
        )
        yield unreachable_workflows
    finally:
        sys.path.remove(str(tmp_path))
        for name in ('unreachable_workflows', 'unreachable_helper'):
            sys.modules.pop(name, None)


@pytest.fixture
def defined_in_main(monkeypatch):
    """Report a class as defined in ``__main__``, the way a notebook cell does.

    Under pytest ``__main__`` is the test runner, which holds no such class, so the worker cannot resolve the name.
    That is exactly the situation in a notebook, whose ``__main__`` is the kernel.
    """

    def _apply(cls):
        monkeypatch.setattr(cls, '__module__', '__main__')
        assert not callables.is_importable(cls)
        return cls

    return _apply


class NotebookWorkChain(WorkChain):
    """Stands in for a class defined in a notebook cell, once ``defined_in_main`` has relabelled it."""

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


def test_workchain_from_a_module_the_daemon_cannot_import(submit_and_await, unreachable_module):
    """Test that a workchain runs on the daemon when only this interpreter can import its module."""
    node = submit_and_await(unreachable_module.UnreachableWorkChain, text=orm.Str('quiet'))

    assert node.is_finished_ok, node.exception
    assert node.outputs.shouted.value == 'QUIET'


def test_workchain_defined_in_main(submit_and_await, defined_in_main):
    """Test that a workchain whose module is ``__main__`` runs on the daemon."""
    node = submit_and_await(defined_in_main(NotebookWorkChain), x=orm.Int(41))

    assert node.is_finished_ok, node.exception
    assert node.outputs.total.value == 42


def test_process_function_defined_in_main(submit_and_await, monkeypatch):
    """Test that a process function whose module is ``__main__`` runs on the daemon.

    A process function is identified by the function rather than by the class built for it, so the function is what
    has to reach the worker.
    """
    from aiida.engine import submit

    monkeypatch.setattr(notebook_add, '__module__', '__main__')
    monkeypatch.setattr(notebook_add.process_class, '__module__', '__main__')

    assert persistence.carried_modules(notebook_add.process_class) is not None, (
        'the daemon can resolve this function, so this test would prove nothing'
    )

    node = submit_and_await(submit(notebook_add, x=orm.Int(41)))

    assert node.is_finished_ok, node.exception
    assert node.outputs.result.value == 42


def test_an_installed_plugin_still_travels_by_name(submit_and_await, aiida_code_installed):
    """Test that a registered plugin carries no payload, which is what keeps an ordinary checkpoint small."""
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    assert persistence.carried_modules(ArithmeticAddCalculation) is None

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.x = orm.Int(2)
    builder.y = orm.Int(40)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.sum.value == 42
    assert node.process_type == 'aiida.calculations:core.arithmetic.add'


def test_shelljob_parser_from_a_module_the_daemon_cannot_import(
    submit_and_await, unreachable_module, aiida_code_installed
):
    """Test that a parser hook reaches the worker together with the module it calls into.

    This is the input case the record model was built for: the node records what the parser is, and the callable
    itself rides the checkpoint, along with a module only the submitting interpreter can import.
    """
    import unreachable_helper

    def parse(dirpath):
        from aiida.orm import Str

        return {'shouted': Str(unreachable_helper.shout((dirpath / 'stdout').read_text().strip()))}

    assert 'unreachable_helper' in persistence.carried_modules(parse)

    code = aiida_code_installed(default_calc_job_plugin='core.shell', filepath_executable='/bin/bash')
    builder = code.get_builder()
    builder.arguments = ['-c', 'echo quiet']
    builder.parser = parse
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}

    # Assigning it to the builder already turned it into an inert record, holding no executable bytes.
    assert isinstance(builder.parser, orm.CallableData)
    assert builder.parser.is_importable is False
    assert 'live_callable' not in builder.parser.base.attributes.all

    node = submit_and_await(builder, timeout=60)

    assert node.is_finished_ok, node.exception
    assert node.outputs.shouted.value == 'QUIET'


def test_calcjob_defined_in_main(submit_and_await, defined_in_main, aiida_code_installed):
    """Test that a calculation job whose module is ``__main__`` runs, and that its outputs are parsed.

    Carrying the class is not enough on its own here: the parser reads the output spec from the process class, and
    asks the running process for it rather than the node, which knows only the name it was recorded under.
    """
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation

    class MainCalcJob(ArithmeticAddCalculation):
        """Stands in for a calculation job defined in a notebook cell."""

        @classmethod
        def define(cls, spec):
            super().define(spec)

    defined_in_main(MainCalcJob)

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
    assert node.base.attributes.get(node.KEY_ATTRIBUTES_CLASS_FINGERPRINT) is not None
    source = textwrap.dedent(node.class_source)
    assert source.startswith('class MainCalcJob(ArithmeticAddCalculation):')
    assert 'super().define(spec)' in source
