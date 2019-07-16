# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm links tests for the export and import routines"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import with_statement

import io
import os
import tarfile
from six.moves import range

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.tools.importexport.utils import get_all_node_links
from aiida.backends.tests.utils.configuration import with_temp_dir
from aiida.common import json
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.common.utils import get_new_uuid
from aiida.tools.importexport import import_data, export


class TestLinks(AiidaTestCase):
    """Test ex-/import cases related to Links"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_links_to_unknown_nodes(self, temp_dir):
        """
        Test importing of nodes, that have links to unknown nodes.
        """
        node_label = "Test structure data"
        struct = orm.StructureData()
        struct.label = str(node_label)
        struct.store()
        struct_uuid = struct.uuid

        filename = os.path.join(temp_dir, "export.tar.gz")
        export([struct], outfile=filename, silent=True)

        unpack = SandboxFolder()
        with tarfile.open(filename, "r:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.extractall(unpack.abspath)

        with io.open(unpack.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
            metadata = json.load(fhandle)
        metadata['links_uuid'].append({
            'output': struct.uuid,
            # note: this uuid is supposed to not be in the DB
            'input': get_new_uuid(),
            'label': 'parent'
        })

        with io.open(unpack.get_abs_path('data.json'), 'wb') as fhandle:
            json.dump(metadata, fhandle)

        with tarfile.open(filename, "w:gz", format=tarfile.PAX_FORMAT) as tar:
            tar.add(unpack.abspath, arcname="")

        self.clean_db()
        self.create_user()

        with self.assertRaises(ValueError):
            import_data(filename, silent=True)

        import_data(filename, ignore_unknown_nodes=True, silent=True)
        self.assertEqual(orm.load_node(struct_uuid).label, node_label)

    @with_temp_dir
    def test_input_and_create_links(self, temp_dir):
        """
        Simple test that will verify that INPUT and CREATE links are properly exported and
        correctly recreated upon import.
        """
        node_work = orm.CalculationNode()
        node_input = orm.Int(1).store()
        node_output = orm.Int(2).store()

        node_work.add_incoming(node_input, LinkType.INPUT_CALC, 'input')
        node_work.store()
        node_output.add_incoming(node_work, LinkType.CREATE, 'output')

        node_work.seal()

        export_links = get_all_node_links()
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([node_output], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)
        import_links = get_all_node_links()

        export_set = [tuple(_) for _ in export_links]
        import_set = [tuple(_) for _ in import_links]

        self.assertSetEqual(set(export_set), set(import_set))

    def construct_complex_graph(self, export_combination=0, work_nodes=None, calc_nodes=None):  # pylint: disable=too-many-statements
        """
        This method creates a "complex" graph with all available link types:
        INPUT_WORK, INPUT_CALC, CALL_WORK, CALL_CALC, CREATE, and RETURN
        and returns the nodes of the graph. It also returns various combinations
        of nodes that need to be extracted but also the final expected set of nodes
        (after adding the expected predecessors, desuccessors).
        """
        if export_combination < 0 or export_combination > 9:
            return None

        if work_nodes is None:
            work_nodes = ["WorkflowNode", "WorkflowNode"]

        if calc_nodes is None:
            calc_nodes = ["orm.CalculationNode", "orm.CalculationNode"]

        # Class mapping
        # "CalcJobNode" is left out, since it is special.
        string_to_class = {
            "WorkflowNode": orm.WorkflowNode,
            "WorkChainNode": orm.WorkChainNode,
            "WorkFunctionNode": orm.WorkFunctionNode,
            "orm.CalculationNode": orm.CalculationNode,
            "CalcFunctionNode": orm.CalcFunctionNode
        }

        # Node creation
        data1 = orm.Int(1).store()
        data2 = orm.Int(1).store()
        work1 = string_to_class[work_nodes[0]]()
        work2 = string_to_class[work_nodes[1]]()

        if calc_nodes[0] == "CalcJobNode":
            calc1 = orm.CalcJobNode()
            calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        else:
            calc1 = string_to_class[calc_nodes[0]]()
        calc1.computer = self.computer

        # Waiting to store Data nodes until they have been "created" with the links below,
        # because @calcfunctions cannot return data, i.e. return stored Data nodes
        data3 = orm.Int(1)
        data4 = orm.Int(1)

        if calc_nodes[1] == "CalcJobNode":
            calc2 = orm.CalcJobNode()
            calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        else:
            calc2 = string_to_class[calc_nodes[1]]()
        calc2.computer = self.computer

        # Waiting to store Data nodes until they have been "created" with the links below,
        # because @calcfunctions cannot return data, i.e. return stored Data nodes
        data5 = orm.Int(1)
        data6 = orm.Int(1)

        # Link creation
        work1.add_incoming(data1, LinkType.INPUT_WORK, 'input1')
        work1.add_incoming(data2, LinkType.INPUT_WORK, 'input2')

        work2.add_incoming(data1, LinkType.INPUT_WORK, 'input1')
        work2.add_incoming(work1, LinkType.CALL_WORK, 'call2')

        work1.store()
        work2.store()

        calc1.add_incoming(data1, LinkType.INPUT_CALC, 'input1')
        calc1.add_incoming(work2, LinkType.CALL_CALC, 'call1')
        calc1.store()

        data3.add_incoming(calc1, LinkType.CREATE, 'create3')
        # data3 is stored now, because a @workfunction cannot return unstored Data,
        # i.e. create data.
        data3.store()
        data3.add_incoming(work2, LinkType.RETURN, 'return3')

        data4.add_incoming(calc1, LinkType.CREATE, 'create4')
        # data3 is stored now, because a @workfunction cannot return unstored Data,
        # i.e. create data.
        data4.store()
        data4.add_incoming(work2, LinkType.RETURN, 'return4')

        calc2.add_incoming(data4, LinkType.INPUT_CALC, 'input4')
        calc2.store()

        data5.add_incoming(calc2, LinkType.CREATE, 'create5')
        data6.add_incoming(calc2, LinkType.CREATE, 'create6')

        data5.store()
        data6.store()

        work1.seal()
        work2.seal()
        calc1.seal()
        calc2.seal()

        graph_nodes = [data1, data2, data3, data4, data5, data6, calc1, calc2, work1, work2]

        # Create various combinations of nodes that should be exported
        # and the final set of nodes that are exported in each case, following
        # predecessor(INPUT, CREATE)/successor(CALL, RETURN, CREATE) links.
        export_list = [(work1, [data1, data2, data3, data4, calc1, work1, work2]),
                       (work2, [data1, data3, data4, calc1, work2]), (data3, [data1, data3, data4, calc1]),
                       (data4, [data1, data3, data4, calc1]), (data5, [data1, data3, data4, data5, data6, calc1,
                                                                       calc2]),
                       (data6, [data1, data3, data4, data5, data6, calc1, calc2]), (calc1, [data1, data3, data4,
                                                                                            calc1]),
                       (calc2, [data1, data3, data4, data5, data6, calc1, calc2]), (data1, [data1]), (data2, [data2])]

        return graph_nodes, export_list[export_combination]

    @with_temp_dir
    def test_data_create_reversed_false(self, temp_dir):
        """Verify that create_reversed = False is respected when only exporting Data nodes."""
        data_input = orm.Int(1).store()
        data_output = orm.Int(2).store()

        calc = orm.CalcJobNode()
        calc.computer = self.computer
        calc.set_option('resources', {"num_machines": 1, "num_mpiprocs_per_machine": 1})

        calc.add_incoming(data_input, LinkType.INPUT_CALC, 'input')
        calc.store()
        data_output.add_incoming(calc, LinkType.CREATE, 'create')
        data_output_uuid = data_output.uuid
        calc.seal()

        group = orm.Group(label='test_group').store()
        group.add_nodes(data_output)

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([group], outfile=export_file, silent=True, create_reversed=False)

        self.reset_database()

        import_data(export_file, silent=True)

        builder = orm.QueryBuilder()
        builder.append(orm.Data)
        self.assertEqual(builder.count(), 1, 'Expected a single Data node but got {}'.format(builder.count()))
        self.assertEqual(builder.all()[0][0].uuid, data_output_uuid)

        builder = orm.QueryBuilder()
        builder.append(orm.CalcJobNode)
        self.assertEqual(builder.count(), 0, 'Expected no Calculation nodes')

    @with_temp_dir
    def test_complex_workflow_graph_links(self, temp_dir):
        """
        This test checks that all the needed links are correctly exported and
        imported. More precisely, it checks that INPUT, CREATE, RETURN and CALL
        links connecting Data nodes, CalcJobNodes and WorkCalculations are
        exported and imported correctly.
        """
        graph_nodes, _ = self.construct_complex_graph()

        # Getting the input, create, return and call links
        builder = orm.QueryBuilder()
        builder.append(orm.Node, project='uuid')
        builder.append(
            orm.Node,
            project='uuid',
            edge_project=['label', 'type'],
            edge_filters={
                'type': {
                    'in': (LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value, LinkType.CREATE.value,
                           LinkType.RETURN.value, LinkType.CALL_CALC.value, LinkType.CALL_WORK.value)
                }
            })
        export_links = builder.all()

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export(graph_nodes, outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)
        import_links = get_all_node_links()

        export_set = [tuple(_) for _ in export_links]
        import_set = [tuple(_) for _ in import_links]

        self.assertSetEqual(set(export_set), set(import_set))

    @with_temp_dir
    def test_complex_workflow_graph_export_sets(self, temp_dir):
        """Test ex-/import of individual nodes in complex graph"""
        for export_conf in range(0, 9):

            _, (export_node, export_target) = self.construct_complex_graph(export_conf)
            export_target_uuids = set(str(_.uuid) for _ in export_target)

            export_file = os.path.join(temp_dir, 'export.tar.gz')
            export([export_node], outfile=export_file, silent=True, overwrite=True)
            export_node_str = str(export_node)

            self.reset_database()

            import_data(export_file, silent=True)

            # Get all the nodes of the database
            builder = orm.QueryBuilder()
            builder.append(orm.Node, project='uuid')
            imported_node_uuids = set(str(_[0]) for _ in builder.all())

            self.assertSetEqual(
                export_target_uuids, imported_node_uuids,
                "Problem in comparison of export node: " + str(export_node_str) + "\n" + "Expected set: " +
                str(export_target_uuids) + "\n" + "Imported set: " + str(imported_node_uuids) + "\n" + "Difference: " +
                str([_ for _ in export_target_uuids.symmetric_difference(imported_node_uuids)]))

    @with_temp_dir
    def test_high_level_workflow_links(self, temp_dir):
        """
        This test checks that all the needed links are correctly exported and imported.
        INPUT_CALC, INPUT_WORK, CALL_CALC, CALL_WORK, CREATE, and RETURN
        links connecting Data nodes and high-level Calculation and Workflow nodes:
        CalcJobNode, CalcFunctionNode, WorkChainNode, WorkFunctionNode
        """
        high_level_calc_nodes = [["CalcJobNode", "CalcJobNode"], ["CalcJobNode", "CalcFunctionNode"],
                                 ["CalcFunctionNode", "CalcJobNode"], ["CalcFunctionNode", "CalcFunctionNode"]]

        high_level_work_nodes = [["WorkChainNode", "WorkChainNode"], ["WorkChainNode", "WorkFunctionNode"],
                                 ["WorkFunctionNode", "WorkChainNode"], ["WorkFunctionNode", "WorkFunctionNode"]]

        for calcs in high_level_calc_nodes:
            for works in high_level_work_nodes:
                self.reset_database()

                graph_nodes, _ = self.construct_complex_graph(calc_nodes=calcs, work_nodes=works)

                # Getting the input, create, return and call links
                builder = orm.QueryBuilder()
                builder.append(orm.Node, project='uuid')
                builder.append(
                    orm.Node,
                    project='uuid',
                    edge_project=['label', 'type'],
                    edge_filters={
                        'type': {
                            'in': (LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value, LinkType.CREATE.value,
                                   LinkType.RETURN.value, LinkType.CALL_CALC.value, LinkType.CALL_WORK.value)
                        }
                    })

                self.assertEqual(
                    builder.count(),
                    13,
                    msg="Failed with c1={}, c2={}, w1={}, w2={}".format(calcs[0], calcs[1], works[0], works[1]))

                export_links = builder.all()

                export_file = os.path.join(temp_dir, 'export.tar.gz')
                export(graph_nodes, outfile=export_file, silent=True, overwrite=True)

                self.reset_database()

                import_data(export_file, silent=True)
                import_links = get_all_node_links()

                export_set = [tuple(_) for _ in export_links]
                import_set = [tuple(_) for _ in import_links]

                self.assertSetEqual(
                    set(export_set),
                    set(import_set),
                    msg="Failed with c1={}, c2={}, w1={}, w2={}".format(calcs[0], calcs[1], works[0], works[1]))

    @with_temp_dir
    def test_links_for_workflows(self, temp_dir):
        """
        Check export flag `return_reversed=True`.
        Check that CALL links are not followed in the export procedure,
        and the only creation is followed for data::

            ____       ____        ____
           |    | INP |    | CALL |    |
           | i1 | --> | w1 | <--- | w2 |
           |____|     |____|      |____|
                        |
                        v RETURN
                       ____
                      |    |
                      | o1 |
                      |____|

        """
        work1 = orm.WorkflowNode()
        work2 = orm.WorkflowNode().store()
        data_in = orm.Int(1).store()
        data_out = orm.Int(2).store()

        work1.add_incoming(data_in, LinkType.INPUT_WORK, 'input_i1')
        work1.add_incoming(work2, LinkType.CALL_WORK, 'call')
        work1.store()
        data_out.add_incoming(work1, LinkType.RETURN, 'returned')

        work1.seal()
        work2.seal()

        links_count_wanted = 2  # All 3 links, except CALL links (the CALL_WORK)
        links_wanted = [
            l for l in get_all_node_links() if l[3] not in (LinkType.CALL_WORK.value, LinkType.CALL_CALC.value)
        ]
        # Check all links except CALL links are retrieved
        self.assertEqual(links_count_wanted, len(links_wanted))

        export_file_1 = os.path.join(temp_dir, 'export-1.tar.gz')
        export_file_2 = os.path.join(temp_dir, 'export-2.tar.gz')
        export([data_out], outfile=export_file_1, silent=True, return_reversed=True)
        export([work1], outfile=export_file_2, silent=True, return_reversed=True)

        self.reset_database()

        import_data(export_file_1, silent=True)
        import_links = get_all_node_links()

        self.assertListEqual(sorted(links_wanted), sorted(import_links))
        self.assertEqual(links_count_wanted, len(import_links))
        self.reset_database()

        import_data(export_file_2, silent=True)
        import_links = get_all_node_links()
        self.assertListEqual(sorted(links_wanted), sorted(import_links))
        self.assertEqual(links_count_wanted, len(import_links))

    @with_temp_dir
    def test_double_return_links_for_workflows(self, temp_dir):
        """
        This test checks that double return links to a node can be exported
        and imported without problems,
        """
        work1 = orm.WorkflowNode()
        work2 = orm.WorkflowNode().store()
        data_in = orm.Int(1).store()
        data_out = orm.Int(2).store()

        work1.add_incoming(data_in, LinkType.INPUT_WORK, 'input_i1')
        work1.add_incoming(work2, LinkType.CALL_WORK, 'call')
        work1.store()
        data_out.add_incoming(work1, LinkType.RETURN, 'return1')
        data_out.add_incoming(work2, LinkType.RETURN, 'return2')
        links_count = 4

        work1.seal()
        work2.seal()

        uuids_wanted = set(_.uuid for _ in (work1, data_out, data_in, work2))
        links_wanted = get_all_node_links()

        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([data_out, work1, work2, data_in], outfile=export_file, silent=True)

        self.reset_database()

        import_data(export_file, silent=True)

        uuids_in_db = [str(uuid) for [uuid] in orm.QueryBuilder().append(orm.Node, project='uuid').all()]
        self.assertListEqual(sorted(uuids_wanted), sorted(uuids_in_db))

        links_in_db = get_all_node_links()
        self.assertListEqual(sorted(links_wanted), sorted(links_in_db))

        # Assert number of links, checking both RETURN links are included
        self.assertEqual(len(links_wanted), links_count)  # Before export
        self.assertEqual(len(links_in_db), links_count)  # After import
