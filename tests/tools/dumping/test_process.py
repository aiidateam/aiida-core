###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.tools._dumping.executors.process`."""

import numpy as np
import pytest

from aiida import orm


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_array_output_without_file_like_sibling(generate_calculation_node, tmp_path):
    """An ``ArrayData`` output is dumped whether or not a file-like output accompanies it.

    Regression test for #7523: ``node_outputs/`` used to be created only when a ``SinglefileData`` or
    ``FolderData`` output was present, while the unfiltered output list was dumped into it. The same
    ``ArrayData`` was therefore written or silently dropped depending on its siblings.
    """
    node = generate_calculation_node(outputs={'arraydata': orm.ArrayData(arrays=np.ones(3))})
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'array-only', include_outputs=True)

    assert (dump_path / 'node_outputs' / 'arraydata' / 'default.npy').is_file()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_array_output_with_file_like_sibling(generate_calculation_node, tmp_path):
    """The ``ArrayData`` of a calculation that also returns a ``SinglefileData`` is dumped alongside it.

    Pairs with :func:`test_dump_array_output_without_file_like_sibling` to pin both sides of the
    sibling dependence, so a regression cannot be hidden by only ever testing the mixed case.
    """
    node = generate_calculation_node(
        outputs={
            'arraydata': orm.ArrayData(arrays=np.ones(3)),
            'singlefile': orm.SinglefileData.from_string(content='a', filename='file.txt'),
        }
    )
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'array-and-file', include_outputs=True)

    assert (dump_path / 'node_outputs' / 'arraydata' / 'default.npy').is_file()
    assert (dump_path / 'node_outputs' / 'singlefile' / 'file.txt').is_file()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dump_database_only_outputs_create_no_directory(generate_calculation_node, tmp_path):
    """Outputs held entirely in the database leave no empty ``node_outputs/`` directory behind."""
    node = generate_calculation_node(outputs={'result': orm.Dict({'answer': 42}), 'count': orm.Int(1)})
    node.seal()

    dump_path = node.dump(output_path=tmp_path / 'database-only', include_outputs=True)

    assert not (dump_path / 'node_outputs').exists()
