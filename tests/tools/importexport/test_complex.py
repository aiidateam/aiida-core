# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Complex tests for the export and import routines"""
# pylint: disable=too-many-locals

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir


class TestComplex(AiidaTestCase):
    """Test complex ex-/import cases"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_complex_graph_import_export(self, temp_dir):
        """
        This test checks that a small and bit complex graph can be correctly
        exported and imported.

        It will create the graph, store it to the database, export it to a file
        and import it. In the end it will check if the initial nodes are present
        at the imported graph.
        """
        from aiida.common.exceptions import NotExistent

        calc1 = orm.CalcJobNode()
        calc1.computer = self.computer
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
        rd1.computer = self.computer
        rd1.store()
        rd1.add_incoming(calc1, link_type=LinkType.CREATE, link_label='link')

        calc2 = orm.CalcJobNode()
        calc2.computer = self.computer
        calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc2.label = 'calc2'
        calc2.add_incoming(pd1, link_type=LinkType.INPUT_CALC, link_label='link1')
        calc2.add_incoming(pd2, link_type=LinkType.INPUT_CALC, link_label='link2')
        calc2.add_incoming(rd1, link_type=LinkType.INPUT_CALC, link_label='link3')
        calc2.store()

        fd1 = orm.FolderData()
        fd1.label = 'fd1'
        fd1.store()
        fd1.add_incoming(calc2, link_type=LinkType.CREATE, link_label='link')

        calc1.seal()
        calc2.seal()

        node_uuids_labels = {
            calc1.uuid: calc1.label,
            pd1.uuid: pd1.label,
            pd2.uuid: pd2.label,
            rd1.uuid: rd1.label,
            calc2.uuid: calc2.label,
            fd1.uuid: fd1.label
        }

        filename = os.path.join(temp_dir, 'export.tar.gz')
        export([fd1], outfile=filename, silent=True)

        self.clean_db()
        self.create_user()

        import_data(filename, silent=True, ignore_unknown_nodes=True)

        for uuid, label in node_uuids_labels.items():
            try:
                orm.load_node(uuid)
            except NotExistent:
                self.fail('Node with UUID {} and label {} was not found.'.format(uuid, label))

    @with_temp_dir
    def test_reexport(self, temp_dir):
        """
        Export something, import and reexport and check if everything is valid.
        The export is rather easy::

            ___       ___          ___
           |   | INP |   | CREATE |   |
           | p | --> | c | -----> | a |
           |___|     |___|        |___|

        """
        import numpy as np
        import string
        import random
        from datetime import datetime

        from aiida.common.hashing import make_hash

        def get_hash_from_db_content(grouplabel):
            """Helper function to get hash"""
            builder = orm.QueryBuilder()
            builder.append(orm.Dict, tag='param', project='*')
            builder.append(orm.CalculationNode, tag='calc', project='*', edge_tag='p2c', edge_project=('label', 'type'))
            builder.append(orm.ArrayData, tag='array', project='*', edge_tag='c2a', edge_project=('label', 'type'))
            builder.append(orm.Group, filters={'label': grouplabel}, project='*', tag='group', with_node='array')
            # I want the query to contain something!
            self.assertTrue(builder.count() > 0)
            # The hash is given from the preservable entries in an export-import cycle,
            # uuids, attributes, labels, descriptions, arrays, link-labels, link-types:
            hash_ = make_hash([(
                item['param']['*'].attributes,
                item['param']['*'].uuid,
                item['param']['*'].label,
                item['param']['*'].description,
                item['calc']['*'].uuid,
                item['calc']['*'].attributes,
                item['array']['*'].attributes,
                [item['array']['*'].get_array(name).tolist() for name in item['array']['*'].get_arraynames()],
                item['array']['*'].uuid,
                item['group']['*'].uuid,
                item['group']['*'].label,
                item['p2c']['label'],
                item['p2c']['type'],
                item['c2a']['label'],
                item['c2a']['type'],
                item['group']['*'].label,
            ) for item in builder.dict()])
            return hash_

        # Creating a folder for the import/export files
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
        param.description = 'd_' + str(datetime.now())
        param.store()
        calc = orm.CalculationNode()
        # setting also trial dict as attributes, but randomizing the keys)
        for key, value in trial_dict.items():
            calc.set_attribute(str(int(key) + np.random.randint(10)), value)
        array = orm.ArrayData()
        array.set_array('array', nparr)
        array.store()
        # LINKS
        # the calculation has input the parameters-instance
        calc.add_incoming(param, link_type=LinkType.INPUT_CALC, link_label='input_parameters')
        calc.store()
        # I want the array to be an output of the calculation
        array.add_incoming(calc, link_type=LinkType.CREATE, link_label='output_array')
        group = orm.Group(label='test-group')
        group.store()
        group.add_nodes(array)

        calc.seal()

        hash_from_dbcontent = get_hash_from_db_content(grouplabel)

        # I export and reimport 3 times in a row:
        for i in range(3):
            # Always new filename:
            filename = os.path.join(temp_dir, 'export-{}.zip'.format(i))
            # Loading the group from the string
            group = orm.Group.get(label=grouplabel)
            # exporting based on all members of the group
            # this also checks if group memberships are preserved!
            export([group] + list(group.nodes), outfile=filename, silent=True)
            # cleaning the DB!
            self.clean_db()
            self.create_user()
            # reimporting the data from the file
            import_data(filename, silent=True, ignore_unknown_nodes=True)
            # creating the hash from db content
            new_hash = get_hash_from_db_content(grouplabel)
            # I check for equality against the first hash created, which implies that hashes
            # are equal in all iterations of this process
            self.assertEqual(hash_from_dbcontent, new_hash)
