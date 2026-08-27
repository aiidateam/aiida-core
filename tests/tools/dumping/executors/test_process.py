###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.tools._dumping.executors.process`."""

import json
import logging
from pathlib import Path

import numpy as np
import pytest

from aiida import orm
from aiida.common import LinkType
from aiida.tools._dumping.executors.process import _nest_by_link_label


def dumped_node_outputs(dump_path: Path) -> list[str]:
    """Return every path under ``node_outputs/``, the directory itself included.

    A calculation that dumps nothing asserts ``[]``; a stray empty ``node_outputs/`` reports
    ``['node_outputs']`` instead, so the two cases the gate decides between stay distinguishable.
    """
    node_outputs = dump_path / 'node_outputs'

    if not node_outputs.exists():
        return []

    paths = [node_outputs, *node_outputs.rglob('*')]

    return sorted(path.relative_to(dump_path).as_posix() for path in paths)


@pytest.fixture
def generate_workflow_node_returning():
    """Return a factory for a sealed ``WorkflowNode`` with a ``RETURN`` link to each of the given nodes."""

    def _generate_workflow_node_returning(returns: dict[str, orm.Data]) -> orm.WorkflowNode:
        workflow_node = orm.WorkflowNode()
        workflow_node.set_process_state('finished')
        workflow_node.store()

        for link_label, returned_node in returns.items():
            # A workflow may only return already stored nodes: it selects results, it does not create them.
            returned_node.store()
            returned_node.base.links.add_incoming(workflow_node, link_type=LinkType.RETURN, link_label=link_label)

        workflow_node.seal()

        return workflow_node

    return _generate_workflow_node_returning


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'make_outputs, expected',
    (
        pytest.param(
            lambda: {'arraydata': orm.ArrayData(arrays=np.ones(3))},
            ['node_outputs', 'node_outputs/arraydata', 'node_outputs/arraydata/default.npy'],
            id='array-only',
        ),
        pytest.param(
            lambda: {
                'arraydata': orm.ArrayData(arrays=np.ones(3)),
                'singlefile': orm.SinglefileData.from_string(content='a', filename='file.txt'),
            },
            [
                'node_outputs',
                'node_outputs/arraydata',
                'node_outputs/arraydata/default.npy',
                'node_outputs/singlefile',
                'node_outputs/singlefile/file.txt',
            ],
            id='array-and-file',
        ),
        pytest.param(lambda: {'result': orm.Dict({'answer': 42}), 'count': orm.Int(1)}, [], id='database-only'),
        pytest.param(lambda: {'folderdata': orm.FolderData()}, [], id='empty-repository'),
    ),
)
def test_node_outputs_gated_on_repository_content(generate_calculation_node, tmp_path, make_outputs, expected):
    """``node_outputs/`` holds exactly those outputs that carry repository content.

    Regression test for #7523: the directory used to be created only when a ``SinglefileData`` or
    ``FolderData`` output was present, while the unfiltered output list was dumped into it. The same
    ``ArrayData`` was therefore written or silently dropped depending on its siblings, so both
    ``array-only`` and ``array-and-file`` are needed to pin the sibling dependence from both sides.
    """
    # The nodes have to be built inside the test: constructing ORM nodes at collection time,
    # in the ``parametrize`` decorator, runs before any profile is loaded.
    node = generate_calculation_node(outputs=make_outputs())
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True)

    assert dumped_node_outputs(dump_path) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dumped_array_round_trips(generate_calculation_node, tmp_path):
    """The dumped ``.npy`` payload is the array that went in, not just a file of the right name."""
    node = generate_calculation_node(outputs={'arraydata': orm.ArrayData(arrays=np.ones(3))})
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True)

    np.testing.assert_array_equal(np.load(dump_path / 'node_outputs' / 'arraydata' / 'default.npy'), np.ones(3))


@pytest.mark.usefixtures('aiida_profile_clean')
def test_data_json_off_by_default(generate_calculation_node, tmp_path):
    """No JSON is written without ``include_data_json``, whatever the outputs are.

    Pins the default behavior the option has to leave untouched: a ``Dict`` result still reaches no file.
    """
    node = generate_calculation_node(outputs={'result': orm.Dict({'answer': 42}), 'count': orm.Int(1)})
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True)

    assert dumped_node_outputs(dump_path) == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_data_json_written_for_non_repository_outputs(generate_calculation_node, tmp_path):
    """``include_data_json`` writes one JSON file per output that carries no repository content.

    The ``ArrayData`` sibling is what discriminates: it has repository content, so it must still be dumped as a
    directory and must not gain a JSON file of its own.
    """
    node = generate_calculation_node(
        outputs={
            'result': orm.Dict({'answer': 42}),
            'count': orm.Int(1),
            'arraydata': orm.ArrayData(arrays=np.ones(3)),
        }
    )
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True, include_data_json=True)

    assert dumped_node_outputs(dump_path) == [
        'node_outputs',
        'node_outputs/arraydata',
        'node_outputs/arraydata/default.npy',
        'node_outputs/count.json',
        'node_outputs/result.json',
    ]
    assert json.loads((dump_path / 'node_outputs' / 'result.json').read_text()) == {'answer': 42}
    assert json.loads((dump_path / 'node_outputs' / 'count.json').read_text()) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_data_json_written_for_empty_repository(generate_calculation_node, tmp_path):
    """An output with an empty repository is written too, as the empty JSON it serializes to.

    The rule is "no repository content, so JSON": a ``FolderData`` that happens to be empty is still an output the
    dump would otherwise pass over in silence.
    """
    node = generate_calculation_node(outputs={'folderdata': orm.FolderData()})
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True, include_data_json=True)

    assert dumped_node_outputs(dump_path) == ['node_outputs', 'node_outputs/folderdata.json']
    assert json.loads((dump_path / 'node_outputs' / 'folderdata.json').read_text()) == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_data_json_written_for_inputs(generate_calculation_node, tmp_path):
    """Inputs are written under ``node_inputs`` on the same terms, and only with ``include_inputs``."""
    node = generate_calculation_node(inputs={'parameters': orm.Dict({'cutoff': 30})})
    # The factory only stores a node that has outputs; an inputs-only node is returned unstored.
    node.store()
    node.seal()

    with_inputs = node.dump(output_path=tmp_path / 'with-inputs', include_data_json=True)
    without_inputs = node.dump(output_path=tmp_path / 'without-inputs', include_inputs=False, include_data_json=True)

    assert json.loads((with_inputs / 'node_inputs' / 'parameters.json').read_text()) == {'cutoff': 30}
    assert not (without_inputs / 'node_inputs').exists()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_data_json_nests_namespaced_link_labels(generate_calculation_node, tmp_path):
    """A namespaced link label is written into one JSON file for the whole namespace.

    ``alphas__filled`` and ``alphas__empty`` come from a single nested output port, so they merge into ``alphas.json``
    rather than becoming two files.
    """
    node = generate_calculation_node(outputs={'alphas__filled': orm.Int(1), 'alphas__empty': orm.Int(2)})
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True, include_data_json=True)

    assert dumped_node_outputs(dump_path) == ['node_outputs', 'node_outputs/alphas.json']
    assert json.loads((dump_path / 'node_outputs' / 'alphas.json').read_text()) == {'filled': 1, 'empty': 2}


@pytest.mark.parametrize(
    'values, expected, warned',
    (
        ({'alphas__filled': 1, 'alphas__empty': 2}, {'alphas': {'filled': 1, 'empty': 2}}, False),
        ({'a': 1, 'a__b': 2}, {'a': 1}, True),
        ({'a': [1, 2], 'a__b': 3}, {'a': [1, 2]}, True),
        ({'a': {'b': 111, 'keep': 1}, 'a__b': 222}, {'a': {'b': 111, 'keep': 1}}, True),
        ({'a__b': {'c': 9}, 'a__b__c': 5}, {'a': {'b': {'c': 9}}}, True),
        ({'deep__a__b__c': 3}, {'deep': {'a': {'b': {'c': 3}}}}, False),
    ),
)
def test_nest_by_link_label_keeps_the_value_that_is_there(values, expected, warned, caplog):
    """A label nested inside another label's value is dropped, whatever that value is.

    The ``Dict``-valued parent is the case that discriminates: merging into it would overwrite the node's own ``b``
    with an unrelated sibling link's value and report nothing. Siblings of one namespace still merge.
    """
    with caplog.at_level(logging.WARNING):
        assert _nest_by_link_label(values) == expected

    assert ('Not writing it' in caplog.text) is warned


@pytest.mark.usefixtures('aiida_profile_clean')
def test_data_json_flat_does_not_overwrite(generate_calculation_node, tmp_path, caplog):
    """Under ``flat`` an input and an output of the same link label compete for one filename; the first one wins.

    ``flat`` puts inputs and outputs in the node directory itself, so ``x`` on both sides names the same file. The
    input is written first, and the output is skipped with a warning rather than overwriting it.
    """
    node = generate_calculation_node(inputs={'x': orm.Int(1)}, outputs={'x': orm.Int(2)})
    node.seal()

    with caplog.at_level(logging.WARNING):
        dump_path = node.dump(output_path=tmp_path / 'dump', include_outputs=True, include_data_json=True, flat=True)

    assert json.loads((dump_path / 'x.json').read_text()) == 1
    assert 'Not writing the JSON of `x` over it' in caplog.text


@pytest.mark.usefixtures('aiida_profile_clean')
def test_workflow_outputs_dumped_without_data_json(generate_workflow_node_returning, tmp_path):
    """``include_workflow_outputs`` gives a ``WorkflowNode`` a ``node_outputs`` directory of the nodes it returned.

    A workflow's ``RETURN`` links reached no file before: the dumper recursed into its children and stopped there.
    The flag stands on its own, so the ``SinglefileData`` return is copied out here with neither ``include_outputs``
    (which governs a calculation's ``CREATE`` outputs) nor ``include_data_json`` set, and the ``Dict`` return is
    passed over for want of the latter.
    """
    node = generate_workflow_node_returning(
        {
            'result': orm.Dict({'answer': 42}),
            'report': orm.SinglefileData.from_string(content='a', filename='file.txt'),
        }
    )

    dump_path = node.dump(output_path=tmp_path / 'dump', include_workflow_outputs=True)

    assert dumped_node_outputs(dump_path) == [
        'node_outputs',
        'node_outputs/report',
        'node_outputs/report/file.txt',
    ]


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'include_workflow_outputs, include_data_json, expected',
    (
        (False, False, []),
        (True, False, []),
        (False, True, []),
        (True, True, ['node_outputs', 'node_outputs/result.json']),
    ),
)
def test_workflow_dict_output_needs_both_options(
    generate_workflow_node_returning, tmp_path, include_workflow_outputs, include_data_json, expected
):
    """A returned ``Dict`` is written only with both options: one opens the directory, the other fills it."""
    node = generate_workflow_node_returning({'result': orm.Dict({'answer': 42})})

    dump_path = node.dump(
        output_path=tmp_path / 'dump',
        include_workflow_outputs=include_workflow_outputs,
        include_data_json=include_data_json,
    )

    assert dumped_node_outputs(dump_path) == expected

    if expected:
        assert json.loads((dump_path / 'node_outputs' / 'result.json').read_text()) == {'answer': 42}
