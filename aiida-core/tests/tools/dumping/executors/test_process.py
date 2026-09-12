###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.tools._dumping.executors.process`."""

from pathlib import Path

import numpy as np
import pytest

from aiida import orm


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
