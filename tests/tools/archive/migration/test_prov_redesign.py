###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the export and import routines related to migration provenance_redesign.

Check changes in database schema after upgrading to v0.4 (Provenance Redesign)
This includes all migrations from "base_data_plugin_type_string" (django: 0008)
until "dbgroup_type_string_change_content" (django: 0022), both included.

The effects of the large db migration "provenance_redesign" (django: 0020)
is tested in `TestLinks`, since the greatest change concerns links.
"""

import pytest

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


def test_base_data_type_change(tmp_path, aiida_profile):
    """Base Data types type string changed
    Example: Bool: “data.base.Bool.” → “data.bool.Bool.”
    """
    aiida_profile.reset_storage()

    # Test content
    test_content = ('Hello', 6, -1.2399834e12, False)
    test_types = ()
    for node_type in ['str', 'int', 'float', 'bool']:
        add_type = (f'data.core.{node_type}.{node_type.capitalize()}.',)
        test_types = test_types.__add__(add_type)

    # List of nodes to be exported
    export_nodes = []

    # Create list of base type nodes
    nodes = [cls(val).store() for val, cls in zip(test_content, (orm.Str, orm.Int, orm.Float, orm.Bool))]
    export_nodes.extend(nodes)

    # Collect uuids for created nodes
    uuids = [n.uuid for n in nodes]

    # Create List() and insert already created nodes into it
    list_node = orm.List()
    list_node.set_list(nodes)
    list_node.store()
    list_node_uuid = list_node.uuid
    export_nodes.append(list_node)

    # Export nodes
    filename = tmp_path / 'export.aiida'
    create_archive(export_nodes, filename=filename)

    # Clean the database
    aiida_profile.reset_storage()

    # Import nodes again
    import_archive(filename)

    # Check whether types are correctly imported
    nlist = orm.load_node(list_node_uuid)  # List
    for uuid, list_value, refval, reftype in zip(uuids, nlist.get_list(), test_content, test_types):
        # Str, Int, Float, Bool
        base = orm.load_node(uuid)
        # Check value/content
        assert base.value == refval
        # Check type
        msg = f"type of node ('{base.node_type}') is not updated according to db schema v0.4"
        assert base.node_type == reftype, msg

        # List
        # Check value
        assert list_value == refval

    # Check List type
    msg = f"type of node ('{nlist.node_type}') is not updated according to db schema v0.4"
    assert nlist.node_type == 'data.core.list.List.', msg


@pytest.mark.requires_rmq
def test_node_process_type(aiida_profile, tmp_path):
    """Column `process_type` added to `Node` entity DB table"""
    from aiida.engine import run_get_node
    from tests.utils.processes import AddProcess

    aiida_profile.reset_storage()

    # Node types
    node_type = 'process.workflow.WorkflowNode.'
    node_process_type = 'tests.utils.processes.AddProcess'

    # Run workflow
    inputs = {'a': orm.Int(2), 'b': orm.Int(3)}
    _, node = run_get_node(AddProcess, **inputs)

    # Save node uuid
    node_uuid = str(node.uuid)

    # Assert correct type and process_type strings
    assert node.node_type == node_type
    assert node.process_type == node_process_type

    # Export nodes
    filename = tmp_path / 'export.aiida'
    create_archive([node], filename=filename)

    # Clean the database and reimport data
    aiida_profile.reset_storage()
    import_archive(filename)

    # Retrieve node and check exactly one node is imported
    builder = orm.QueryBuilder()
    builder.append(orm.ProcessNode, project=['uuid'])

    assert builder.count() == 1

    # Get node uuid and check it is the same as the one exported
    nodes = builder.all()
    imported_node_uuid = str(nodes[0][0])

    assert imported_node_uuid == node_uuid

    # Check imported node type and process type
    node = orm.load_node(imported_node_uuid)

    assert node.node_type == node_type
    assert node.process_type == node_process_type


@pytest.mark.usefixtures('suppress_internal_deprecations')
def test_code_type_change(aiida_profile, tmp_path, aiida_localhost):
    """Code type string changed
    Change: “code.Bool.” → “data.code.Code.”
    """
    # Create Code instance
    code = orm.Code((aiida_localhost, '/bin/true')).store()

    # Save uuid and type
    code_uuid = str(code.uuid)
    code_type = code.node_type

    # Assert correct type exists prior to export
    assert code_type == 'data.core.code.Code.'

    # Export node
    filename = tmp_path / 'export.aiida'
    create_archive([code], filename=filename)

    # Clean the database and reimport
    aiida_profile.reset_storage()
    import_archive(filename)

    # Retrieve Code node and make sure exactly 1 is retrieved
    builder = orm.QueryBuilder()
    builder.append(orm.Code, project=['uuid'])
    imported_code = builder.all()

    assert builder.count() == 1

    # Check uuid is the same after import
    imported_code_uuid = str(imported_code[0][0])

    assert imported_code_uuid == code_uuid

    # Check whether types are correctly imported
    imported_code_type = orm.load_node(imported_code_uuid).node_type

    assert imported_code_type == code_type


def test_group_name_and_type_change(tmp_path, aiida_profile):
    """Group's name and type columns have changed
    Change for columns:
    “name”            --> “label”
    "type"            --> "type_string"
    Furthermore, type_strings have been updated to:
    ""                --> "user"
    "data.upf.family" --> "data.upf"
    "aiida.import"    --> "auto.import"
    "autogroup.run"   --> "auto.run"

    The new columns are called on group instances, and will fail if not present.
    A user created Group is validated to have the "user" value as a type_string.
    A UPF file is created and imported/uploaded as a UPF family,
    in order to create a Group with type_string="data.upf".
    Any import will create a Group with type_string "auto.import", which is checked.
    The type_string="auto.run" is not directly checked, but if the three checks
    above succeed, it is understood that "auto.run" is also correctly ex-/imported
    as the type_string content for the relevant Groups.
    """
    from aiida.orm.nodes.data.upf import upload_upf_family

    aiida_profile.reset_storage()

    # To be saved
    groups_label = ['Users', 'UpfData']
    upf_filename = 'Al.test_file.UPF'
    # regular upf file version 2 header
    upf_contents = '\n'.join(  # noqa: FLY002
        [
            '<UPF version="2.0.1">',
            'Human readable section is completely irrelevant for parsing!',
            '<PP_HEADER',
            'contents before element tag',
            'element="Al"',
            'contents following element tag',
            '>',
        ]
    )
    with (tmp_path / upf_filename).open('w') as upf_file:
        upf_file.write(upf_contents)

    # Create Groups
    node1 = orm.CalculationNode().store()
    node2 = orm.CalculationNode().store()
    node1.seal()
    node2.seal()
    group_user = orm.Group(label=groups_label[0]).store()
    group_user.add_nodes([node1, node2])

    upload_upf_family(str(tmp_path), groups_label[1], '')
    group_upf = orm.load_group(groups_label[1])

    # Save uuids and type
    groups_uuid = [str(g.uuid) for g in [group_user, group_upf]]
    groups_type_string = [g.type_string for g in [group_user, group_upf]]

    # Assert correct type strings exists prior to export
    assert groups_type_string == ['core', 'core.upf']

    # Export node
    filename = tmp_path / 'export.aiida'
    create_archive([group_user, group_upf], filename=filename)

    # Clean the database and reimport
    aiida_profile.reset_storage()
    import_archive(filename)

    # Retrieve Groups and make sure exactly 3 are retrieved (including the "import group")
    builder = orm.QueryBuilder()
    builder.append(orm.Group, project=['uuid'])
    imported_groups = builder.all()

    assert builder.count() == 3

    # Check uuids are the same after import
    imported_groups_uuid = [str(g[0]) for g in imported_groups]

    # We do not know the "import group"'s uuid, so go through known uuids
    for group_uuid in groups_uuid:
        assert group_uuid in imported_groups_uuid

        # Pop known uuid from imported_groups_uuid, eventually leaving
        # only the "import group"
        imported_groups_uuid.remove(group_uuid)

        # Load group
        imported_group = orm.load_group(group_uuid)

        # Check whether types are correctly imported
        assert imported_group.type_string in groups_type_string

        # Assert labels are imported correctly
        assert imported_group.label in groups_label

    # Check type_string content of "import group"
    import_group = orm.load_group(imported_groups_uuid[0])
    assert import_group.type_string == 'core.import'
