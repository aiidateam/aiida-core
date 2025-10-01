###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Complex tests for the export and import routines"""

import random
import string
from datetime import datetime

import numpy as np

from aiida import orm
from aiida.common.exceptions import NotExistent
from aiida.common.hashing import make_hash
from aiida.common.links import LinkType
from aiida.tools.archive import create_archive, import_archive


def test_complex_graph_import_export(aiida_profile_clean, tmp_path, aiida_localhost):
    """This test checks that a small and bit complex graph can be correctly
    exported and imported.

    It will create the graph, store it to the database, export it to a file
    and import it. In the end it will check if the initial nodes are present
    at the imported graph.
    """
    calc1 = orm.CalcJobNode()
    calc1.computer = aiida_localhost
    calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    calc1.label = 'calc1'
    calc1.store()

    pd1 = orm.Dict()
    pd1.label = 'pd1'
    pd1.store()

    pd2 = orm.Dict()
    pd2.label = 'pd2'
    pd2.store()

    rd1 = orm.RemoteData()
    rd1.label = 'rd1'
    rd1.set_remote_path('/x/y.py')
    rd1.computer = aiida_localhost
    rd1.store()
    rd1.base.links.add_incoming(calc1, link_type=LinkType.CREATE, link_label='link')

    calc2 = orm.CalcJobNode()
    calc2.computer = aiida_localhost
    calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    calc2.label = 'calc2'
    calc2.base.links.add_incoming(pd1, link_type=LinkType.INPUT_CALC, link_label='link1')
    calc2.base.links.add_incoming(pd2, link_type=LinkType.INPUT_CALC, link_label='link2')
    calc2.base.links.add_incoming(rd1, link_type=LinkType.INPUT_CALC, link_label='link3')
    calc2.store()

    fd1 = orm.FolderData()
    fd1.label = 'fd1'
    fd1.store()
    fd1.base.links.add_incoming(calc2, link_type=LinkType.CREATE, link_label='link')

    calc1.seal()
    calc2.seal()

    node_uuids_labels = {
        calc1.uuid: calc1.label,
        pd1.uuid: pd1.label,
        pd2.uuid: pd2.label,
        rd1.uuid: rd1.label,
        calc2.uuid: calc2.label,
        fd1.uuid: fd1.label,
    }

    filename = tmp_path / 'export.aiida'
    create_archive([fd1], filename=filename)

    aiida_profile_clean.reset_storage()

    import_archive(filename)

    for uuid, label in node_uuids_labels.items():
        try:
            orm.load_node(uuid)
        except NotExistent:
            raise NotExistent(f'Node with UUID {uuid} and label {label} was not found.')


def test_reexport(aiida_profile_clean, tmp_path):
    """Export something, import and re-export and check if everything is valid.
    The export is rather easy::

        ___       ___          ___
        |   | INP |   | CREATE |   |
        | p | --> | c | -----> | a |
        |___|     |___|        |___|

    """
    # Creating a folder for the archive files
    chars = string.ascii_uppercase + string.digits
    size = 10
    grouplabel = 'test-group'

    nparr = np.random.random((4, 3, 2))
    trial_dict = {}
    # give some integers:
    trial_dict.update({str(k): np.random.randint(100) for k in range(10)})
    # give some floats:
    trial_dict.update({str(k): np.random.random() for k in range(10, 20)})
    # give some booleans:
    trial_dict.update({str(k): bool(np.random.randint(1)) for k in range(20, 30)})
    # give some text:
    trial_dict.update({str(k): ''.join(random.choice(chars) for _ in range(size)) for k in range(20, 30)})

    param = orm.Dict(dict=trial_dict)
    param.label = str(datetime.now())
    param.description = f'd_{datetime.now()!s}'
    param.store()
    calc = orm.CalculationNode()
    # setting also trial dict as attributes, but randomizing the keys)
    for key, value in trial_dict.items():
        calc.base.attributes.set(str(int(key) + np.random.randint(10)), value)
    array = orm.ArrayData()
    array.set_array('array', nparr)
    array.store()
    # LINKS
    # the calculation has input the parameters-instance
    calc.base.links.add_incoming(param, link_type=LinkType.INPUT_CALC, link_label='input_parameters')
    calc.store()
    # I want the array to be an output of the calculation
    array.base.links.add_incoming(calc, link_type=LinkType.CREATE, link_label='output_array')
    group = orm.Group(label='test-group')
    group.store()
    group.add_nodes(array)

    calc.seal()

    hash_from_dbcontent = get_hash_from_db_content(grouplabel)

    # I export and reimport 3 times in a row:
    for i in range(3):
        # Always new filename:
        filename = tmp_path / f'export-{i}.aiida'
        # Loading the group from the string
        group = orm.Group.collection.get(label=grouplabel)
        # exporting based on all members of the group
        # this also checks if group memberships are preserved!
        create_archive([group] + list(group.nodes), filename=filename)
        # cleaning the DB!
        aiida_profile_clean.reset_storage()
        # reimporting the data from the file
        import_archive(filename)
        # creating the hash from db content
        new_hash = get_hash_from_db_content(grouplabel)
        # I check for equality against the first hash created, which implies that hashes
        # are equal in all iterations of this process
        assert hash_from_dbcontent == new_hash


def get_hash_from_db_content(grouplabel):
    """Helper function to get hash"""
    builder = orm.QueryBuilder()
    builder.append(orm.Dict, tag='param', project='*')
    builder.append(orm.CalculationNode, tag='calc', project='*', edge_tag='p2c', edge_project=('label', 'type'))
    builder.append(orm.ArrayData, tag='array', project='*', edge_tag='c2a', edge_project=('label', 'type'))
    builder.append(orm.Group, filters={'label': grouplabel}, project='*', tag='group', with_node='array')
    # I want the query to contain something!
    assert builder.count() > 0
    # The hash is given from the preservable entries in an export-import cycle,
    # uuids, attributes, labels, descriptions, arrays, link-labels, link-types:
    hash_ = make_hash(
        [
            (
                item['param']['*'].base.attributes.all,
                item['param']['*'].uuid,
                item['param']['*'].label,
                item['param']['*'].description,
                item['calc']['*'].uuid,
                item['calc']['*'].base.attributes.all,
                item['array']['*'].base.attributes.all,
                [item['array']['*'].get_array(name).tolist() for name in item['array']['*'].get_arraynames()],
                item['array']['*'].uuid,
                item['group']['*'].uuid,
                item['group']['*'].label,
                item['p2c']['label'],
                item['p2c']['type'],
                item['c2a']['label'],
                item['c2a']['type'],
                item['group']['*'].label,
            )
            for item in builder.dict()
        ]
    )
    return hash_


def test_complex_export_filter_size(tmp_path, aiida_profile_clean):
    """Test export with various entity types when filter_size limits are exceeded."""
    # Create multiple entity types to test different code paths
    nb_entities = 10

    # Create users (will need nodes attached to be exported)
    users = []
    for i in range(nb_entities):
        user = orm.User(email=f'user{i}@example.com').store()
        users.append(user)

    # Create nodes with different users
    nodes = []
    for i, user in enumerate(users):
        node = orm.Int(i, user=user)
        node.label = f'node_{i}'
        node.store()
        nodes.append(node)

    # Create some links between nodes
    calc_nodes = []
    for i in range(min(3, nb_entities)):
        calc = orm.CalculationNode()
        calc.base.links.add_incoming(nodes[i], LinkType.INPUT_CALC, f'input_{i}')
        calc.store()
        calc.seal()
        calc_nodes.append(calc)
        nodes.append(calc)

    # Export with small filter_size to force batching in multiple functions
    export_file = tmp_path / 'large_export.aiida'
    create_archive(nodes, filename=export_file, filter_size=3)

    # Verify by importing
    aiida_profile_clean.reset_storage()
    import_archive(export_file)

    # Check all entities were properly exported/imported
    assert orm.QueryBuilder().append(orm.Node).count() == len(nodes)
    assert orm.QueryBuilder().append(orm.User).count() == nb_entities + 1  # +1 for default user

    # Assert for calculation nodes specifically
    calc_node_count = orm.QueryBuilder().append(orm.CalculationNode).count()
    assert calc_node_count == len(calc_nodes)

    # Assert for data nodes specifically
    data_node_count = orm.QueryBuilder().append(orm.Int).count()
    assert data_node_count == nb_entities

    # Verify links were preserved
    link_count = orm.QueryBuilder().append(entity_type='link').count()
    assert link_count >= 3  # At least the links we created
