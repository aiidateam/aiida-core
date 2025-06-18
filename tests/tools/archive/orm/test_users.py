###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.User tests for the export and import routines"""

from aiida import orm
from aiida.tools.archive import create_archive, import_archive


def test_nodes_belonging_to_different_users(aiida_profile, tmp_path, aiida_localhost):
    """This test checks that nodes belonging to different users are correctly
    exported & imported.
    """
    from aiida.common.links import LinkType
    from aiida.manage import get_manager

    manager = get_manager()

    # Create another user
    new_email = 'newuser@new.n'
    user = orm.User(email=new_email).store()

    # Create a structure data node that has a calculation as output
    sd1 = orm.StructureData(pbc=False)
    sd1.user = user
    sd1.label = 'sd1'
    sd1.store()

    jc1 = orm.CalcJobNode()
    jc1.computer = aiida_localhost
    jc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    jc1.user = user
    jc1.label = 'jc1'
    jc1.base.links.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')
    jc1.store()

    # Create some nodes from a different user
    sd2 = orm.StructureData(pbc=False)
    sd2.user = user
    sd2.label = 'sd2'
    sd2.store()
    sd2.base.links.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')  # I assume jc1 CREATED sd2
    jc1.seal()

    jc2 = orm.CalcJobNode()
    jc2.computer = aiida_localhost
    jc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    jc2.label = 'jc2'
    jc2.base.links.add_incoming(sd2, link_type=LinkType.INPUT_CALC, link_label='l2')
    jc2.store()

    sd3 = orm.StructureData(pbc=False)
    sd3.label = 'sd3'
    sd3.store()
    sd3.base.links.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')
    jc2.seal()

    uuids_u1 = [sd1.uuid, jc1.uuid, sd2.uuid]
    uuids_u2 = [jc2.uuid, sd3.uuid]

    filename = tmp_path.joinpath('export.aiida')

    create_archive([sd3], filename=filename)
    aiida_profile.reset_storage()
    import_archive(filename)

    # Check that the imported nodes are correctly imported and that
    # the user assigned to the nodes is the right one
    for uuid in uuids_u1:
        node = orm.load_node(uuid=uuid)
        assert node.user.email == new_email
    for uuid in uuids_u2:
        assert orm.load_node(uuid).user.email == manager.get_profile().default_user_email


def test_non_default_user_nodes(aiida_profile_clean, tmp_path, aiida_localhost_factory):
    """This test checks that nodes belonging to user A (which is not the
    default user) can be correctly exported, imported, enriched with nodes
    from the default user, re-exported & re-imported and that in the end
    all the nodes that have been finally imported belonging to the right
    users.
    """
    from aiida.common.links import LinkType
    from aiida.manage import get_manager

    manager = get_manager()

    # Create another user
    new_email = 'newuser@new.n'
    user = orm.User(email=new_email).store()

    # Create a structure data node that has a calculation as output
    sd1 = orm.StructureData(pbc=False)
    sd1.user = user
    sd1.label = 'sd1'
    sd1.store()

    jc1 = orm.CalcJobNode()
    jc1.computer = aiida_localhost_factory()
    jc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    jc1.user = user
    jc1.label = 'jc1'
    jc1.base.links.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')
    jc1.store()

    # Create some nodes from a different user
    sd2 = orm.StructureData(pbc=False)
    sd2.user = user
    sd2.label = 'sd2'
    sd2.base.links.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')
    sd2.store()
    jc1.seal()
    sd2_uuid = sd2.uuid

    # At this point we export the generated data
    filename1 = tmp_path.joinpath('export1.aiidaz')
    create_archive([sd2], filename=filename1)
    uuids1 = [sd1.uuid, jc1.uuid, sd2.uuid]
    aiida_profile_clean.reset_storage()
    import_archive(filename1)

    # Check that the imported nodes are correctly imported and that
    # the user assigned to the nodes is the right one
    for uuid in uuids1:
        assert orm.load_node(uuid).user.email == new_email

    # Now we continue to generate more data based on the imported
    # data
    sd2_imp = orm.load_node(sd2_uuid)

    jc2 = orm.CalcJobNode()
    jc2.computer = aiida_localhost_factory()
    jc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    jc2.label = 'jc2'
    jc2.base.links.add_incoming(sd2_imp, link_type=LinkType.INPUT_CALC, link_label='l2')
    jc2.store()

    sd3 = orm.StructureData(pbc=False)
    sd3.label = 'sd3'
    sd3.base.links.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')
    sd3.store()
    jc2.seal()

    # Store the UUIDs of the nodes that should be checked
    # if they can be imported correctly.
    uuids2 = [jc2.uuid, sd3.uuid]

    filename2 = tmp_path.joinpath('export2.aiida')
    create_archive([sd3], filename=filename2)
    aiida_profile_clean.reset_storage()
    import_archive(filename2)

    # Check that the imported nodes are correctly imported and that
    # the user assigned to the nodes is the right one
    for uuid in uuids1:
        assert orm.load_node(uuid).user.email == new_email
    for uuid in uuids2:
        assert orm.load_node(uuid).user.email == manager.get_profile().default_user_email


def test_filter_size(tmp_path, aiida_profile_clean):
    """Tests if the query still works when the number of users is beyond the `filter_size limit."""
    nb_nodes = 5
    nodes = []
    # We need to attach a node to the user otherwise it is not exported
    for i in range(nb_nodes):
        node = orm.Int(5, user=orm.User(email=f'{i}').store())
        node.store()
        nodes.append(node)

    # Export DB
    export_file_existing = tmp_path.joinpath('export.aiida')
    create_archive(nodes, filename=export_file_existing)

    # Clean database and reimport DB
    aiida_profile_clean.reset_storage()
    import_archive(export_file_existing, filter_size=2)

    # Check correct import
    builder = orm.QueryBuilder().append(orm.User, project=['id'])
    builder = builder.all()

    # We need to add one because default profile is added by reset_storage
    # automatically
    assert len(builder) == nb_nodes + 1
