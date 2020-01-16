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

import os
import tarfile

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import json
from aiida.common.folders import SandboxFolder
from aiida.common.links import LinkType
from aiida.common.utils import get_new_uuid
from aiida.tools.importexport import import_data, export
from aiida.tools.importexport.common.exceptions import DanglingLinkError

from tests.utils.configuration import with_temp_dir
from tests.tools.importexport.utils import get_all_node_links


class TestLinks(AiidaTestCase):
    """Test ex-/import cases related to Links"""

    def setUp(self):
        self.reset_database()
        super().setUp()

    def tearDown(self):
        self.reset_database()
        super().tearDown()

    @with_temp_dir
    def test_links_to_unknown_nodes(self, temp_dir):
        """Test importing of nodes, that have links to unknown nodes."""
        node_label = 'Test structure data'
        struct = orm.StructureData()
        struct.label = str(node_label)
        struct.store()
        struct_uuid = struct.uuid

        filename = os.path.join(temp_dir, 'export.tar.gz')
        export([struct], outfile=filename, silent=True)

        unpack = SandboxFolder()
        with tarfile.open(filename, 'r:gz', format=tarfile.PAX_FORMAT) as tar:
            tar.extractall(unpack.abspath)

        with open(unpack.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
            data = json.load(fhandle)
        data['links_uuid'].append({
            'output': struct.uuid,
            # note: this uuid is supposed to not be in the DB:
            'input': get_new_uuid(),
            'label': 'parent',
            'type': LinkType.CREATE.value
        })

        with open(unpack.get_abs_path('data.json'), 'wb') as fhandle:
            json.dump(data, fhandle)

        with tarfile.open(filename, 'w:gz', format=tarfile.PAX_FORMAT) as tar:
            tar.add(unpack.abspath, arcname='')

        self.reset_database()

        with self.assertRaises(DanglingLinkError):
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

        Graph::

            data1 ---------------INPUT_WORK----------------+
              |                                            |
              |     data2 -INPUT_WORK-+                    |
              |                       V                    V
              +-------INPUT_WORK--> work1 --CALL_WORK--> work2 ----+
              |                                            |       |
              |              CALL_CALC---------------------+       |
              |                  |            +-> data3 <-+        |
              |                  V            |           |        |
              +--INPUT_CALC--> calc1 --CREATE-+-> data4 <-+-----RETURN       +-> data5
                                                    |                        |
                                                INPUT_CALC--> calc2 --CREATE-+-> data6

        """
        if export_combination < 0 or export_combination > 9:
            return None

        if work_nodes is None:
            work_nodes = ['WorkflowNode', 'WorkflowNode']

        if calc_nodes is None:
            calc_nodes = ['CalculationNode', 'CalculationNode']

        # Class mapping
        # "CalcJobNode" is left out, since it is special.
        string_to_class = {
            'WorkflowNode': orm.WorkflowNode,
            'WorkChainNode': orm.WorkChainNode,
            'WorkFunctionNode': orm.WorkFunctionNode,
            'CalculationNode': orm.CalculationNode,
            'CalcFunctionNode': orm.CalcFunctionNode
        }

        # Node creation
        data1 = orm.Int(1).store()
        data2 = orm.Int(1).store()
        work1 = string_to_class[work_nodes[0]]()
        work2 = string_to_class[work_nodes[1]]()

        if calc_nodes[0] == 'CalcJobNode':
            calc1 = orm.CalcJobNode()
            calc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        else:
            calc1 = string_to_class[calc_nodes[0]]()
        calc1.computer = self.computer

        # Waiting to store Data nodes until they have been "created" with the links below,
        # because @calcfunctions cannot return data, i.e. return stored Data nodes
        data3 = orm.Int(1)
        data4 = orm.Int(1)

        if calc_nodes[1] == 'CalcJobNode':
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
                       (work2, [data1, data3, data4, calc1, work2, work1, data2]),
                       (data3, [data1, data3, data4, calc1, work2, work1, data2]),
                       (data4, [data1, data3, data4, calc1, work2, work1, data2]),
                       (data5, [data1, data3, data4, data5, data6, calc1, calc2, work2, work1, data2]),
                       (data6, [data1, data3, data4, data5, data6, calc1, calc2, work2, work1, data2]),
                       (calc1, [data1, data3, data4, calc1, work2, work1, data2]),
                       (calc2, [data1, data3, data4, data5, data6, calc1, calc2, work2, work1, data2]),
                       (data1, [data1]), (data2, [data2])]

        return graph_nodes, export_list[export_combination]

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
                    'in': (
                        LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value, LinkType.CREATE.value,
                        LinkType.RETURN.value, LinkType.CALL_CALC.value, LinkType.CALL_WORK.value
                    )
                }
            }
        )
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
            export_target_uuids = set(_.uuid for _ in export_target)

            export_file = os.path.join(temp_dir, 'export.tar.gz')
            export([export_node], outfile=export_file, silent=True, overwrite=True)
            export_node_str = str(export_node)

            self.reset_database()

            import_data(export_file, silent=True)

            # Get all the nodes of the database
            builder = orm.QueryBuilder()
            builder.append(orm.Node, project='uuid')
            imported_node_uuids = set(_[0] for _ in builder.all())

            self.assertSetEqual(
                export_target_uuids, imported_node_uuids,
                'Problem in comparison of export node: ' + export_node_str + '\n' + 'Expected set: ' +
                str(export_target_uuids) + '\n' + 'Imported set: ' + str(imported_node_uuids) + '\n' + 'Difference: ' +
                str(export_target_uuids.symmetric_difference(imported_node_uuids))
            )

    @with_temp_dir
    def test_high_level_workflow_links(self, temp_dir):
        """
        This test checks that all the needed links are correctly exported and imported.
        INPUT_CALC, INPUT_WORK, CALL_CALC, CALL_WORK, CREATE, and RETURN
        links connecting Data nodes and high-level Calculation and Workflow nodes:
        CalcJobNode, CalcFunctionNode, WorkChainNode, WorkFunctionNode
        """
        high_level_calc_nodes = [['CalcJobNode', 'CalcJobNode'], ['CalcJobNode', 'CalcFunctionNode'],
                                 ['CalcFunctionNode', 'CalcJobNode'], ['CalcFunctionNode', 'CalcFunctionNode']]

        high_level_work_nodes = [['WorkChainNode', 'WorkChainNode'], ['WorkChainNode', 'WorkFunctionNode'],
                                 ['WorkFunctionNode', 'WorkChainNode'], ['WorkFunctionNode', 'WorkFunctionNode']]

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
                            'in': (
                                LinkType.INPUT_CALC.value, LinkType.INPUT_WORK.value, LinkType.CREATE.value,
                                LinkType.RETURN.value, LinkType.CALL_CALC.value, LinkType.CALL_WORK.value
                            )
                        }
                    }
                )

                self.assertEqual(
                    builder.count(),
                    13,
                    msg='Failed with c1={}, c2={}, w1={}, w2={}'.format(calcs[0], calcs[1], works[0], works[1])
                )

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
                    msg='Failed with c1={}, c2={}, w1={}, w2={}'.format(calcs[0], calcs[1], works[0], works[1])
                )

    @staticmethod
    def prepare_link_flags_export(nodes_to_export, test_data):
        """Helper function"""
        from aiida.common.links import GraphTraversalRules

        export_rules = GraphTraversalRules.EXPORT.value
        traversal_rules = {name: rule.default for name, rule in export_rules.items() if rule.toggleable}

        for export_file, rule_changes, expected_nodes in test_data.values():
            traversal_rules.update(rule_changes)
            export(nodes_to_export[0], outfile=export_file, silent=True, **traversal_rules)

            for node_type in nodes_to_export[1]:
                if node_type in expected_nodes:
                    expected_nodes[node_type].update(nodes_to_export[1][node_type])
                else:
                    expected_nodes[node_type] = nodes_to_export[1][node_type]

    def link_flags_import_helper(self, test_data):
        """Helper function"""
        for test, (export_file, _, expected_nodes) in test_data.items():
            self.reset_database()

            import_data(export_file, silent=True)

            nodes_util = {'work': orm.WorkflowNode, 'calc': orm.CalculationNode, 'data': orm.Data}
            for node_type, node_cls in nodes_util.items():
                if node_type in expected_nodes:
                    builder = orm.QueryBuilder().append(node_cls, project='uuid')
                    self.assertEqual(
                        builder.count(),
                        len(expected_nodes[node_type]),
                        msg='Expected {} {} node(s), but got {}. Test: "{}"'.format(
                            len(expected_nodes[node_type]), node_type, builder.count(), test
                        )
                    )
                    for node_uuid in builder.iterall():
                        self.assertIn(node_uuid[0], expected_nodes[node_type], msg='Failed for test: "{}"'.format(test))

    def link_flags_export_helper(self, name, all_nodes, temp_dir, nodes_to_export, flags, expected_nodes):  # pylint: disable=too-many-arguments
        """Helper function"""
        (calc_flag, work_flag) = flags
        (export_types, nodes_to_export) = nodes_to_export
        (expected_types, expected_nodes_temp) = expected_nodes

        export_nodes_uuid = {_: set() for _ in export_types}
        for node in nodes_to_export:
            for node_type in export_nodes_uuid:
                if node.startswith(node_type):
                    export_nodes_uuid[node_type].update({all_nodes[node]['uuid']})
        nodes_to_export = ([all_nodes[_]['node'] for _ in nodes_to_export], export_nodes_uuid)

        expected_nodes = []
        for expected_node_list in expected_nodes_temp:
            expected_nodes_uuid = {_: set() for _ in expected_types}
            for node in expected_node_list:
                for node_type in expected_nodes_uuid:
                    if node.startswith(node_type):
                        expected_nodes_uuid[node_type].update({all_nodes[node]['uuid']})
            expected_nodes.append(expected_nodes_uuid)

        ret = {
            '{}_follow_none'.format(name): (
                os.path.join(temp_dir, '{}_none.aiida'.format(name)), {
                    calc_flag: False,
                    work_flag: False
                }, expected_nodes[0]
            ),
            '{}_follow_only_calc'.format(name): (
                os.path.join(temp_dir, '{}_calc.aiida'.format(name)), {
                    calc_flag: True,
                    work_flag: False
                }, expected_nodes[1]
            ),
            '{}_follow_only_work'.format(name): (
                os.path.join(temp_dir, '{}_work.aiida'.format(name)), {
                    calc_flag: False,
                    work_flag: True
                }, expected_nodes[2]
            ),
            '{}_follow_only_all'.format(name): (
                os.path.join(temp_dir, '{}_all.aiida'.format(name)), {
                    calc_flag: True,
                    work_flag: True
                }, expected_nodes[3]
            )
        }

        self.prepare_link_flags_export(nodes_to_export, ret)
        return ret

    @with_temp_dir
    def test_link_flags(self, temp_dir):
        """Verify all link follow flags are working as intended.

        Graph (from ``self.construct_complex_graph()``)::

            data1 ---------------INPUT_WORK----------------+
              |                                            |
              |     data2 -INPUT_WORK-+                    |
              |                       V                    V
              +-------INPUT_WORK--> work1 --CALL_WORK--> work2 ----+
              |                                            |       |
              |              CALL_CALC---------------------+       |
              |                  |            +-> data3 <-+        |
              |                  V            |           |        |
              +--INPUT_CALC--> calc1 --CREATE-+-> data4 <-+-----RETURN       +-> data5
                                                    |                        |
                                                INPUT_CALC--> calc2 --CREATE-+-> data6

        """
        graph_nodes, _ = self.construct_complex_graph()
        # The first 6 are data nodes 1-6, then the two calc nodes, and finally the two work nodes.
        nodes = {}
        skip = 0
        for node_type, i in [('data', 6), ('calc', 2), ('work', 2)]:
            for j in range(i):
                key = node_type + str(j + 1)
                nodes[key] = {'node': graph_nodes[j + skip]}
                nodes[key]['uuid'] = nodes[key]['node'].uuid
            skip += i

        # input links - forward
        input_links_forward = self.link_flags_export_helper(
            'input_links_forward',
            nodes,
            temp_dir,
            nodes_to_export=(['data'], ['data1']),
            flags=('input_calc_forward', 'input_work_forward'),
            expected_nodes=(
                ['data', 'calc', 'work'],
                [
                    [],  # calc: False, work: False (DEFAULT)
                    ['calc1', 'data3', 'data4', 'calc2', 'data5', 'data6', 'work2', 'work1',
                     'data2'],  # calc: True, work: False
                    ['work1', 'data2', 'work2', 'calc1', 'data3', 'data4'],  # calc: False, work: True
                    ['work1', 'data2', 'work2', 'calc1', 'data3', 'data4', 'calc2', 'data5',
                     'data6']  # calc: True, work: True
                ]
            )
        )

        # create/return links - backward
        create_return_links_backward = self.link_flags_export_helper(
            'create_return_links_backward',
            nodes,
            temp_dir,
            nodes_to_export=(['data'], ['data4', 'data5']),
            flags=('create_backward', 'return_backward'),
            expected_nodes=(
                ['data', 'calc', 'work'],
                [
                    [],  # create: False, return: False
                    ['calc1', 'data3', 'data1', 'calc2', 'data6', 'work2', 'work1',
                     'data2'],  # create: True, return: False (DEFAULT)
                    ['work2', 'data1', 'calc1', 'data3', 'work1', 'data2'],  # create: False, return: True
                    ['calc1', 'data3', 'data1', 'work2', 'calc2', 'data6', 'work1',
                     'data2']  # create: True, return: True
                ]
            )
        )

        # call links - backward (Exporting calc1)
        # Not checking difference between (calc: False, work: False) and (calc: False, work: True),
        # making this extra check below.
        call_links_backward_calc1 = self.link_flags_export_helper(
            'call_links_backward_calc1',
            nodes,
            temp_dir,
            nodes_to_export=(['calc'], ['calc1']),
            flags=('call_calc_backward', 'call_work_backward'),
            expected_nodes=(
                ['data', 'work'],
                [
                    ['data1', 'data3', 'data4'],  # calc: False, work: False
                    ['data1', 'data3', 'data4', 'work2'],  # calc: True, work: False
                    ['data1', 'data3', 'data4'],  # calc: False, work: True
                    ['data1', 'data3', 'data4', 'work2', 'work1', 'data2']  # calc: True, work: True (DEFAULT)
                ]
            )
        )

        # call links - backward (Exporting work2)
        # Extra, to check difference between (calc: False, work: False) and (calc: False, work: True)
        call_links_backward_work2 = self.link_flags_export_helper(
            'call_links_backward_work2',
            nodes,
            temp_dir,
            nodes_to_export=(['work'], ['work2']),
            flags=('call_calc_backward', 'call_work_backward'),
            expected_nodes=(
                ['data', 'calc', 'work'],
                [
                    ['data1', 'calc1', 'data3', 'data4'],  # calc: False, work: False
                    ['data1', 'calc1', 'data3', 'data4'],  # calc: True, work: False
                    ['data1', 'calc1', 'data3', 'data4', 'work1', 'data2'],  # calc: False, work: True
                    ['data1', 'calc1', 'data3', 'data4', 'work1', 'data2']  # calc: True, work: True (DEFAULT)
                ]
            )
        )

        self.link_flags_import_helper(input_links_forward)
        self.link_flags_import_helper(create_return_links_backward)
        self.link_flags_import_helper(call_links_backward_calc1)
        self.link_flags_import_helper(call_links_backward_work2)

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

    @with_temp_dir
    def test_dangling_link_to_existing_db_node(self, temp_dir):
        """A dangling link that references a Node that is not included in the archive should `not` be importable"""
        struct = orm.StructureData()
        struct.store()
        struct_uuid = struct.uuid

        calc = orm.CalculationNode()
        calc.add_incoming(struct, LinkType.INPUT_CALC, 'input')
        calc.store()
        calc.seal()
        calc_uuid = calc.uuid

        filename = os.path.join(temp_dir, 'export.tar.gz')
        export([struct], outfile=filename, silent=True)

        unpack = SandboxFolder()
        with tarfile.open(filename, 'r:gz', format=tarfile.PAX_FORMAT) as tar:
            tar.extractall(unpack.abspath)

        with open(unpack.get_abs_path('data.json'), 'r', encoding='utf8') as fhandle:
            data = json.load(fhandle)
        data['links_uuid'].append({
            'output': calc.uuid,
            'input': struct.uuid,
            'label': 'input',
            'type': LinkType.INPUT_CALC.value
        })

        with open(unpack.get_abs_path('data.json'), 'wb') as fhandle:
            json.dump(data, fhandle)

        with tarfile.open(filename, 'w:gz', format=tarfile.PAX_FORMAT) as tar:
            tar.add(unpack.abspath, arcname='')

        # Make sure the CalculationNode is still in the database
        builder = orm.QueryBuilder().append(orm.CalculationNode, project='uuid')
        self.assertEqual(
            builder.count(),
            1,
            msg='There should be a single CalculationNode, instead {} has been found'.format(builder.count())
        )
        self.assertEqual(builder.all()[0][0], calc_uuid)

        with self.assertRaises(DanglingLinkError):
            import_data(filename, silent=True)

        # Using the flag `ignore_unknown_nodes` should import it without problems
        import_data(filename, ignore_unknown_nodes=True, silent=True)
        builder = orm.QueryBuilder().append(orm.StructureData, project='uuid')
        self.assertEqual(
            builder.count(),
            1,
            msg='There should be a single StructureData, instead {} has been found'.format(builder.count())
        )
        self.assertEqual(builder.all()[0][0], struct_uuid)

    @with_temp_dir
    def test_multiple_post_return_links(self, temp_dir):  # pylint: disable=too-many-locals
        """Check extra RETURN links can be added to existing Nodes, when label is not unique"""
        data = orm.Int(1).store()
        calc = orm.CalculationNode().store()
        work = orm.WorkflowNode().store()
        link_label = 'output_data'

        data.add_incoming(calc, LinkType.CREATE, link_label)
        data.add_incoming(work, LinkType.RETURN, link_label)

        calc.seal()
        work.seal()

        data_uuid = data.uuid
        calc_uuid = calc.uuid
        work_uuid = work.uuid
        before_links = get_all_node_links()

        data_provenance = os.path.join(temp_dir, 'data.aiida')
        all_provenance = os.path.join(temp_dir, 'all.aiida')

        export([data], outfile=data_provenance, silent=True, return_backward=False)
        export([data], outfile=all_provenance, silent=True, return_backward=True)

        self.reset_database()

        # import data provenance
        import_data(data_provenance, silent=True)

        no_of_work = orm.QueryBuilder().append(orm.WorkflowNode).count()
        self.assertEqual(
            no_of_work, 0, msg='{} WorkflowNode(s) was/were found, however, none should be present'.format(no_of_work)
        )

        nodes = orm.QueryBuilder().append(orm.Node, project='uuid')
        self.assertEqual(
            nodes.count(),
            2,
            msg='{} Node(s) was/were found, however, exactly two should be present'.format(no_of_work)
        )
        for node in nodes.iterall():
            self.assertIn(node[0], [data_uuid, calc_uuid])

        links = get_all_node_links()
        self.assertEqual(
            len(links),
            1,
            msg='Only a single Link (from Calc. to Data) is expected, '
            'instead {} were found (in, out, label, type): {}'.format(len(links), links)
        )
        for from_uuid, to_uuid, found_label, found_type in links:
            self.assertEqual(from_uuid, calc_uuid)
            self.assertEqual(to_uuid, data_uuid)
            self.assertEqual(found_label, link_label)
            self.assertEqual(found_type, LinkType.CREATE.value)

        # import data+logic provenance
        import_data(all_provenance, silent=True)

        no_of_work = orm.QueryBuilder().append(orm.WorkflowNode).count()
        self.assertEqual(
            no_of_work,
            1,
            msg='{} WorkflowNode(s) was/were found, however, exactly one should be present'.format(no_of_work)
        )

        nodes = orm.QueryBuilder().append(orm.Node, project='uuid')
        self.assertEqual(
            nodes.count(),
            3,
            msg='{} Node(s) was/were found, however, exactly three should be present'.format(no_of_work)
        )
        for node in nodes.iterall():
            self.assertIn(node[0], [data_uuid, calc_uuid, work_uuid])

        links = get_all_node_links()
        self.assertEqual(
            len(links),
            2,
            msg='Exactly two Links are expected, instead {} were found '
            '(in, out, label, type): {}'.format(len(links), links)
        )
        self.assertListEqual(sorted(links), sorted(before_links))
