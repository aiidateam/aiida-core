###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the export and import routines"""

import numpy as np

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


def test_simple_import(aiida_profile_clean, tmp_path):
    """This is a very simple test which checks that an archive file with nodes
    that are not associated to a computer is imported correctly. In Django
    when such nodes are exported, there is an empty set for computers
    in the archive file. In SQLA there is such a set only when a computer is
    associated with the exported nodes. When an empty computer set is
    found at the archive file (when imported to an SQLA profile), the SQLA
    import code used to crash. This test demonstrates this problem.
    """
    parameters = orm.Dict(
        dict={
            'Pr': {'cutoff': 50.0, 'pseudo_type': 'Wentzcovitch', 'dual': 8, 'cutoff_units': 'Ry'},
            'Ru': {'cutoff': 40.0, 'pseudo_type': 'SG15', 'dual': 4, 'cutoff_units': 'Ry'},
        }
    ).store()

    archive_path = tmp_path / 'archive.aiida'

    nodes = [parameters]
    create_archive(nodes, filename=archive_path)

    # Check that we have the expected number of nodes in the database
    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)

    # Clean the database and verify there are no nodes left
    aiida_profile_clean.reset_storage()
    assert orm.QueryBuilder().append(orm.Node).count() == 0

    # After importing we should have the original number of nodes again
    import_archive(archive_path)
    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)


def test_cycle_structure_data(aiida_profile_clean, aiida_localhost, tmp_path):
    """Create an export with some orm.CalculationNode and Data nodes and import it after having
    cleaned the database. Verify that the nodes and their attributes are restored
    properly after importing the created export archive
    """
    from aiida.common.links import LinkType

    test_label = 'Test structure'
    test_cell = [
        [8.34, 0.0, 0.0],
        [0.298041701839357, 8.53479766274308, 0.0],
        [0.842650688117053, 0.47118495164127, 10.6965192730702],
    ]
    test_kinds = [
        {'symbols': ['Fe'], 'weights': [1.0], 'mass': 55.845, 'name': 'Fe'},
        {'symbols': ['S'], 'weights': [1.0], 'mass': 32.065, 'name': 'S'},
    ]

    structure = orm.StructureData(cell=test_cell)
    structure.append_atom(symbols=['Fe'], position=[0, 0, 0])
    structure.append_atom(symbols=['S'], position=[2, 2, 2])
    structure.label = test_label
    structure.store()

    parent_process = orm.CalculationNode()
    parent_process.base.attributes.set('key', 'value')
    parent_process.store()
    child_calculation = orm.CalculationNode()
    child_calculation.base.attributes.set('key', 'value')
    remote_folder = orm.RemoteData(computer=aiida_localhost, remote_path='/').store()

    remote_folder.base.links.add_incoming(parent_process, link_type=LinkType.CREATE, link_label='link')
    child_calculation.base.links.add_incoming(remote_folder, link_type=LinkType.INPUT_CALC, link_label='link')
    child_calculation.store()
    structure.base.links.add_incoming(child_calculation, link_type=LinkType.CREATE, link_label='link')

    parent_process.seal()
    child_calculation.seal()

    archive_path = tmp_path / 'archive.aiida'

    nodes = [structure, child_calculation, parent_process, remote_folder]
    create_archive(nodes, filename=archive_path)

    # Check that we have the expected number of nodes in the database
    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)

    # Clean the database and verify there are no nodes left
    aiida_profile_clean.reset_storage()
    assert orm.QueryBuilder().append(orm.Node).count() == 0

    # After importing we should have the original number of nodes again
    import_archive(archive_path)
    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)

    # Verify that orm.CalculationNodes have non-empty attribute dictionaries
    builder = orm.QueryBuilder().append(orm.CalculationNode)
    for [calculation] in builder.iterall():
        assert isinstance(calculation.base.attributes.all, dict)
        assert len(calculation.base.attributes.all) != 0

    # Verify that the structure data maintained its label, cell and kinds
    builder = orm.QueryBuilder().append(orm.StructureData)
    for [structure] in builder.iterall():
        assert structure.label == test_label
        # Check that they are almost the same, within numerical precision
        assert np.abs(np.array(structure.cell) - np.array(test_cell)).max() < 1.0e-12

    builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
    for [kinds] in builder.iterall():
        assert len(kinds) == 2
        for kind in kinds:
            assert kind in test_kinds

    # Check that there is a StructureData that is an output of a orm.CalculationNode
    builder = orm.QueryBuilder()
    builder.append(orm.CalculationNode, project=['uuid'], tag='calculation')
    builder.append(orm.StructureData, with_incoming='calculation')
    assert len(builder.all()) > 0

    # Check that there is a RemoteData that is a child and parent of a orm.CalculationNode
    builder = orm.QueryBuilder()
    builder.append(orm.CalculationNode, tag='parent')
    builder.append(orm.RemoteData, project=['uuid'], with_incoming='parent', tag='remote')
    builder.append(orm.CalculationNode, with_incoming='remote')
    assert len(builder.all()) > 0


def test_import_checkpoints(aiida_profile_clean, tmp_path):
    """Check that process node checkpoints are stripped when importing.

    The process node checkpoints need to be stripped because they
    could be maliciously crafted to execute arbitrary code, since
    we use the `yaml.UnsafeLoader` to load them.
    """
    node = orm.WorkflowNode().store()
    node.set_checkpoint(12)
    node.seal()
    node_uuid = node.uuid
    assert node.checkpoint == 12

    archive_path = tmp_path / 'archive.aiida'
    nodes = [node]
    create_archive(nodes, filename=archive_path)

    # Check that we have the expected number of nodes in the database
    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)

    # Clean the database and verify there are no nodes left
    aiida_profile_clean.reset_storage()
    assert orm.QueryBuilder().append(orm.Node).count() == 0

    import_archive(archive_path)

    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)
    node_new = orm.load_node(node_uuid)
    assert node_new.checkpoint is None
