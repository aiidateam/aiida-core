###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm links tests for the export and import routines"""

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.orm.entities import EntityTypes
from aiida.tools.archive import create_archive, import_archive
from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip
from tests.tools.archive.utils import get_all_node_links


def test_links_to_unknown_nodes(tmp_path, aiida_profile_clean):
    """Test importing of nodes, that have links to unknown nodes."""
    # store a node
    node = orm.Data()
    node.label = 'Test structure data'
    node.store()

    # create an archive with the structure node
    filename = tmp_path.joinpath('export.aiida')
    create_archive([node], filename=filename)

    # now append a link to a node that does not exist
    # note, because we enforce foreign keys, this would fail anyway in the archive creation
    with ArchiveFormatSqlZip().open(filename, 'a', _enforce_foreign_keys=False) as archive:
        archive.bulk_insert(
            EntityTypes.LINK,
            [
                {
                    'id': 1,
                    'input_id': 99999,
                    'output_id': node.pk,
                    'label': 'parent',
                    'type': LinkType.CREATE.value,
                }
            ],
        )

    # the link should now be in the archive
    with ArchiveFormatSqlZip().open(filename, 'r') as archive:
        assert archive.querybuilder().append(entity_type='link').count() == 1

    aiida_profile_clean.reset_storage()

    # since the query builder only looks for links between known nodes,
    # this should not import the erroneous link
    import_archive(filename)

    assert orm.QueryBuilder().append(orm.Node).count() == 1
    assert orm.QueryBuilder().append(entity_type='link').count() == 0


def test_input_and_create_links(tmp_path, aiida_profile_clean):
    """Simple test that will verify that INPUT and CREATE links are properly exported and
    correctly recreated upon import.
    """
    node_work = orm.CalculationNode()
    node_input = orm.Int(1).store()
    node_output = orm.Int(2).store()

    node_work.base.links.add_incoming(node_input, LinkType.INPUT_CALC, 'input')
    node_work.store()
    node_output.base.links.add_incoming(node_work, LinkType.CREATE, 'output')

    node_work.seal()

    export_links = get_all_node_links()
    export_file = tmp_path.joinpath('export.aiida')
    create_archive([node_output], filename=export_file)

    aiida_profile_clean.reset_storage()

    import_archive(export_file)
    import_links = get_all_node_links()

    export_set = [tuple(_) for _ in export_links]
    import_set = [tuple(_) for _ in import_links]

    assert set(export_set) == set(import_set)


def construct_complex_graph(aiida_localhost_factory, export_combination=0, work_nodes=None, calc_nodes=None):
    """This method creates a "complex" graph with all available link types:
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
        'CalcFunctionNode': orm.CalcFunctionNode,
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
    calc1.computer = aiida_localhost_factory()

    # Waiting to store Data nodes until they have been "created" with the links below,
    # because @calcfunctions cannot return data, i.e. return stored Data nodes
    data3 = orm.Int(1)
    data4 = orm.Int(1)

    if calc_nodes[1] == 'CalcJobNode':
        calc2 = orm.CalcJobNode()
        calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    else:
        calc2 = string_to_class[calc_nodes[1]]()
    calc2.computer = aiida_localhost_factory()

    # Waiting to store Data nodes until they have been "created" with the links below,
    # because @calcfunctions cannot return data, i.e. return stored Data nodes
    data5 = orm.Int(1)
    data6 = orm.Int(1)

    # Link creation
    work1.base.links.add_incoming(data1, LinkType.INPUT_WORK, 'input1')
    work1.base.links.add_incoming(data2, LinkType.INPUT_WORK, 'input2')

    work2.base.links.add_incoming(data1, LinkType.INPUT_WORK, 'input1')
    work2.base.links.add_incoming(work1, LinkType.CALL_WORK, 'call2')

    work1.store()
    work2.store()

    calc1.base.links.add_incoming(data1, LinkType.INPUT_CALC, 'input1')
    calc1.base.links.add_incoming(work2, LinkType.CALL_CALC, 'call1')
    calc1.store()

    data3.base.links.add_incoming(calc1, LinkType.CREATE, 'create3')
    # data3 is stored now, because a @workfunction cannot return unstored Data,
    # i.e. create data.
    data3.store()
    data3.base.links.add_incoming(work2, LinkType.RETURN, 'return3')

    data4.base.links.add_incoming(calc1, LinkType.CREATE, 'create4')
    # data3 is stored now, because a @workfunction cannot return unstored Data,
    # i.e. create data.
    data4.store()
    data4.base.links.add_incoming(work2, LinkType.RETURN, 'return4')

    calc2.base.links.add_incoming(data4, LinkType.INPUT_CALC, 'input4')
    calc2.store()

    data5.base.links.add_incoming(calc2, LinkType.CREATE, 'create5')
    data6.base.links.add_incoming(calc2, LinkType.CREATE, 'create6')

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
    export_list = [
        (work1, [data1, data2, data3, data4, calc1, work1, work2]),
        (work2, [data1, data3, data4, calc1, work2, work1, data2]),
        (data3, [data1, data3, data4, calc1, work2, work1, data2]),
        (data4, [data1, data3, data4, calc1, work2, work1, data2]),
        (data5, [data1, data3, data4, data5, data6, calc1, calc2, work2, work1, data2]),
        (data6, [data1, data3, data4, data5, data6, calc1, calc2, work2, work1, data2]),
        (calc1, [data1, data3, data4, calc1, work2, work1, data2]),
        (calc2, [data1, data3, data4, data5, data6, calc1, calc2, work2, work1, data2]),
        (data1, [data1]),
        (data2, [data2]),
    ]

    return graph_nodes, export_list[export_combination]


def test_complex_workflow_graph_links(aiida_profile_clean, tmp_path, aiida_localhost_factory):
    """This test checks that all the needed links are correctly exported and
    imported. More precisely, it checks that INPUT, CREATE, RETURN and CALL
    links connecting Data nodes, CalcJobNodes and WorkCalculations are
    exported and imported correctly.
    """
    graph_nodes, _ = construct_complex_graph(aiida_localhost_factory)

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
                    LinkType.INPUT_CALC.value,
                    LinkType.INPUT_WORK.value,
                    LinkType.CREATE.value,
                    LinkType.RETURN.value,
                    LinkType.CALL_CALC.value,
                    LinkType.CALL_WORK.value,
                )
            }
        },
    )
    export_links = builder.all()

    export_file = tmp_path.joinpath('export.aiida')
    create_archive(graph_nodes, filename=export_file)

    aiida_profile_clean.reset_storage()

    import_archive(export_file)
    import_links = get_all_node_links()

    export_set = [tuple(_) for _ in export_links]
    import_set = [tuple(_) for _ in import_links]

    assert set(export_set) == set(import_set)


@pytest.mark.nightly
def test_complex_workflow_graph_export_sets(aiida_profile_clean, tmp_path, aiida_localhost_factory):
    """Test ex-/import of individual nodes in complex graph"""
    for export_conf in range(0, 9):
        _, (export_node, export_target) = construct_complex_graph(aiida_localhost_factory, export_conf)
        export_target_uuids = set(_.uuid for _ in export_target)

        export_file = tmp_path.joinpath('export.aiida')
        create_archive([export_node], filename=export_file, overwrite=True)
        export_node_str = str(export_node)

        aiida_profile_clean.reset_storage()

        import_archive(export_file)

        # Get all the nodes of the database
        builder = orm.QueryBuilder()
        builder.append(orm.Node, project='uuid')
        imported_node_uuids = set(_[0] for _ in builder.all())

        assert export_target_uuids == imported_node_uuids, (
            'Problem in comparison of export node: '
            + export_node_str
            + '\n'
            + 'Expected set: '
            + str(export_target_uuids)
            + '\n'
            + 'Imported set: '
            + str(imported_node_uuids)
            + '\n'
            + 'Difference: '
            + str(export_target_uuids.symmetric_difference(imported_node_uuids))
        )


@pytest.mark.nightly
def test_high_level_workflow_links(aiida_profile_clean, tmp_path, aiida_localhost_factory):
    """This test checks that all the needed links are correctly exported and imported.
    INPUT_CALC, INPUT_WORK, CALL_CALC, CALL_WORK, CREATE, and RETURN
    links connecting Data nodes and high-level Calculation and Workflow nodes:
    CalcJobNode, CalcFunctionNode, WorkChainNode, WorkFunctionNode
    """
    high_level_calc_nodes = [
        ['CalcJobNode', 'CalcJobNode'],
        ['CalcJobNode', 'CalcFunctionNode'],
        ['CalcFunctionNode', 'CalcJobNode'],
        ['CalcFunctionNode', 'CalcFunctionNode'],
    ]

    high_level_work_nodes = [
        ['WorkChainNode', 'WorkChainNode'],
        ['WorkChainNode', 'WorkFunctionNode'],
        ['WorkFunctionNode', 'WorkChainNode'],
        ['WorkFunctionNode', 'WorkFunctionNode'],
    ]

    for calcs in high_level_calc_nodes:
        for works in high_level_work_nodes:
            aiida_profile_clean.reset_storage()

            graph_nodes, _ = construct_complex_graph(aiida_localhost_factory, calc_nodes=calcs, work_nodes=works)

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
                            LinkType.INPUT_CALC.value,
                            LinkType.INPUT_WORK.value,
                            LinkType.CREATE.value,
                            LinkType.RETURN.value,
                            LinkType.CALL_CALC.value,
                            LinkType.CALL_WORK.value,
                        )
                    }
                },
            )

            assert builder.count() == 13, f'Failed with c1={calcs[0]}, c2={calcs[1]}, w1={works[0]}, w2={works[1]}'

            export_links = builder.all()

            export_file = tmp_path.joinpath('export.aiida')
            create_archive(graph_nodes, filename=export_file, overwrite=True)

            aiida_profile_clean.reset_storage()

            import_archive(export_file)
            import_links = get_all_node_links()

            export_set = [tuple(_) for _ in export_links]
            import_set = [tuple(_) for _ in import_links]

            assert set(export_set) == set(
                import_set
            ), f'Failed with c1={calcs[0]}, c2={calcs[1]}, w1={works[0]}, w2={works[1]}'


def prepare_link_flags_export(nodes_to_export, test_data):
    """Helper function"""
    from aiida.common.links import GraphTraversalRules

    export_rules = GraphTraversalRules.EXPORT.value
    traversal_rules = {name: rule.default for name, rule in export_rules.items() if rule.toggleable}

    for export_file, rule_changes, expected_nodes in test_data.values():
        traversal_rules.update(rule_changes)
        create_archive(nodes_to_export[0], filename=export_file, **traversal_rules)

        for node_type in nodes_to_export[1]:
            if node_type in expected_nodes:
                expected_nodes[node_type].update(nodes_to_export[1][node_type])
            else:
                expected_nodes[node_type] = nodes_to_export[1][node_type]


def link_flags_import_helper(test_data, reset_db):
    """Helper function"""
    for test, (export_file, _, expected_nodes) in test_data.items():
        reset_db()

        import_archive(export_file)

        nodes_util = {'work': orm.WorkflowNode, 'calc': orm.CalculationNode, 'data': orm.Data}
        for node_type, node_cls in nodes_util.items():
            if node_type in expected_nodes:
                builder = orm.QueryBuilder().append(node_cls, project='uuid')
                assert builder.count() == len(
                    expected_nodes[node_type]
                ), 'Expected {} {} node(s), but got {}. Test: "{}"'.format(
                    len(expected_nodes[node_type]), node_type, builder.count(), test
                )
                for node_uuid in builder.iterall():
                    assert node_uuid[0] in expected_nodes[node_type], f'Failed for test: "{test}"'


def link_flags_export_helper(name, all_nodes, tmp_path, nodes_to_export, flags, expected_nodes):
    """Helper function"""
    (calc_flag, work_flag) = flags
    (export_types, nodes_to_export) = nodes_to_export
    (expected_types, expected_nodes_temp) = expected_nodes

    export_nodes_uuid = {_: set() for _ in export_types}
    for node in nodes_to_export:
        for node_type in export_nodes_uuid:  # noqa: PLC0206
            if node.startswith(node_type):
                export_nodes_uuid[node_type].update({all_nodes[node]['uuid']})
    nodes_to_export = ([all_nodes[_]['node'] for _ in nodes_to_export], export_nodes_uuid)

    expected_nodes = []
    for expected_node_list in expected_nodes_temp:
        expected_nodes_uuid = {_: set() for _ in expected_types}
        for node in expected_node_list:
            for node_type in expected_nodes_uuid:  # noqa: PLC0206
                if node.startswith(node_type):
                    expected_nodes_uuid[node_type].update({all_nodes[node]['uuid']})
        expected_nodes.append(expected_nodes_uuid)

    ret = {
        f'{name}_follow_none': (
            tmp_path.joinpath(f'{name}_none.aiida'),
            {calc_flag: False, work_flag: False},
            expected_nodes[0],
        ),
        f'{name}_follow_only_calc': (
            tmp_path.joinpath(f'{name}_calc.aiida'),
            {calc_flag: True, work_flag: False},
            expected_nodes[1],
        ),
        f'{name}_follow_only_work': (
            tmp_path.joinpath(f'{name}_work.aiida'),
            {calc_flag: False, work_flag: True},
            expected_nodes[2],
        ),
        f'{name}_follow_only_all': (
            tmp_path.joinpath(f'{name}_all.aiida'),
            {calc_flag: True, work_flag: True},
            expected_nodes[3],
        ),
    }

    prepare_link_flags_export(nodes_to_export, ret)
    return ret


@pytest.mark.nightly
def test_link_flags(aiida_profile_clean, tmp_path, aiida_localhost_factory):
    """Verify all link follow flags are working as intended.

    Graph (from ``construct_complex_graph()``)::

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
    graph_nodes, _ = construct_complex_graph(aiida_localhost_factory)
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
    input_links_forward = link_flags_export_helper(
        'input_links_forward',
        nodes,
        tmp_path,
        nodes_to_export=(['data'], ['data1']),
        flags=('input_calc_forward', 'input_work_forward'),
        expected_nodes=(
            ['data', 'calc', 'work'],
            [
                [],  # calc: False, work: False (DEFAULT)
                [
                    'calc1',
                    'data3',
                    'data4',
                    'calc2',
                    'data5',
                    'data6',
                    'work2',
                    'work1',
                    'data2',
                ],  # calc: True, work: False
                ['work1', 'data2', 'work2', 'calc1', 'data3', 'data4'],  # calc: False, work: True
                [
                    'work1',
                    'data2',
                    'work2',
                    'calc1',
                    'data3',
                    'data4',
                    'calc2',
                    'data5',
                    'data6',
                ],  # calc: True, work: True
            ],
        ),
    )

    # create/return links - backward
    create_return_links_backward = link_flags_export_helper(
        'create_return_links_backward',
        nodes,
        tmp_path,
        nodes_to_export=(['data'], ['data4', 'data5']),
        flags=('create_backward', 'return_backward'),
        expected_nodes=(
            ['data', 'calc', 'work'],
            [
                [],  # create: False, return: False
                [
                    'calc1',
                    'data3',
                    'data1',
                    'calc2',
                    'data6',
                    'work2',
                    'work1',
                    'data2',
                ],  # create: True, return: False (DEFAULT)
                ['work2', 'data1', 'calc1', 'data3', 'work1', 'data2'],  # create: False, return: True
                ['calc1', 'data3', 'data1', 'work2', 'calc2', 'data6', 'work1', 'data2'],  # create: True, return: True
            ],
        ),
    )

    # call links - backward (Exporting calc1)
    # Not checking difference between (calc: False, work: False) and (calc: False, work: True),
    # making this extra check below.
    call_links_backward_calc1 = link_flags_export_helper(
        'call_links_backward_calc1',
        nodes,
        tmp_path,
        nodes_to_export=(['calc'], ['calc1']),
        flags=('call_calc_backward', 'call_work_backward'),
        expected_nodes=(
            ['data', 'work'],
            [
                ['data1', 'data3', 'data4'],  # calc: False, work: False
                ['data1', 'data3', 'data4', 'work2'],  # calc: True, work: False
                ['data1', 'data3', 'data4'],  # calc: False, work: True
                ['data1', 'data3', 'data4', 'work2', 'work1', 'data2'],  # calc: True, work: True (DEFAULT)
            ],
        ),
    )

    # call links - backward (Exporting work2)
    # Extra, to check difference between (calc: False, work: False) and (calc: False, work: True)
    call_links_backward_work2 = link_flags_export_helper(
        'call_links_backward_work2',
        nodes,
        tmp_path,
        nodes_to_export=(['work'], ['work2']),
        flags=('call_calc_backward', 'call_work_backward'),
        expected_nodes=(
            ['data', 'calc', 'work'],
            [
                ['data1', 'calc1', 'data3', 'data4'],  # calc: False, work: False
                ['data1', 'calc1', 'data3', 'data4'],  # calc: True, work: False
                ['data1', 'calc1', 'data3', 'data4', 'work1', 'data2'],  # calc: False, work: True
                ['data1', 'calc1', 'data3', 'data4', 'work1', 'data2'],  # calc: True, work: True (DEFAULT)
            ],
        ),
    )

    link_flags_import_helper(input_links_forward, aiida_profile_clean.reset_storage)
    link_flags_import_helper(create_return_links_backward, aiida_profile_clean.reset_storage)
    link_flags_import_helper(call_links_backward_calc1, aiida_profile_clean.reset_storage)
    link_flags_import_helper(call_links_backward_work2, aiida_profile_clean.reset_storage)


def test_double_return_links_for_workflows(tmp_path, aiida_profile_clean):
    """This test checks that double return links to a node can be exported
    and imported without problems,
    """
    work1 = orm.WorkflowNode()
    work2 = orm.WorkflowNode().store()
    data_in = orm.Int(1).store()
    data_out = orm.Int(2).store()

    work1.base.links.add_incoming(data_in, LinkType.INPUT_WORK, 'input_i1')
    work1.base.links.add_incoming(work2, LinkType.CALL_WORK, 'call')
    work1.store()
    data_out.base.links.add_incoming(work1, LinkType.RETURN, 'return1')
    data_out.base.links.add_incoming(work2, LinkType.RETURN, 'return2')
    links_count = 4

    work1.seal()
    work2.seal()

    uuids_wanted = set(_.uuid for _ in (work1, data_out, data_in, work2))
    links_wanted = get_all_node_links()

    export_file = tmp_path.joinpath('export.aiida')
    create_archive([data_out, work1, work2, data_in], filename=export_file)

    aiida_profile_clean.reset_storage()

    import_archive(export_file)

    uuids_in_db = [str(uuid) for [uuid] in orm.QueryBuilder().append(orm.Node, project='uuid').all()]
    assert sorted(uuids_wanted) == sorted(uuids_in_db)

    links_in_db = get_all_node_links()
    assert sorted(links_wanted) == sorted(links_in_db)

    # Assert number of links, checking both RETURN links are included
    assert len(links_wanted) == links_count  # Before export
    assert len(links_in_db) == links_count  # After import


def test_multiple_post_return_links(tmp_path, aiida_profile_clean):
    """Check extra RETURN links can be added to existing Nodes, when label is not unique"""
    data = orm.Int(1).store()
    calc = orm.CalculationNode().store()
    work = orm.WorkflowNode().store()
    link_label = 'output_data'

    data.base.links.add_incoming(calc, LinkType.CREATE, link_label)
    data.base.links.add_incoming(work, LinkType.RETURN, link_label)

    calc.seal()
    work.seal()

    data_uuid = data.uuid
    calc_uuid = calc.uuid
    work_uuid = work.uuid
    before_links = get_all_node_links()

    data_provenance = tmp_path.joinpath('data.core.aiida')
    all_provenance = tmp_path.joinpath('all.aiida')

    create_archive([data], filename=data_provenance, return_backward=False)
    create_archive([data], filename=all_provenance, return_backward=True)

    aiida_profile_clean.reset_storage()

    # import data provenance
    import_archive(data_provenance)

    no_of_work = orm.QueryBuilder().append(orm.WorkflowNode).count()
    assert no_of_work == 0, f'{no_of_work} WorkflowNode(s) was/were found, however, none should be present'

    nodes = orm.QueryBuilder().append(orm.Node, project='uuid')
    assert nodes.count() == 2, f'{no_of_work} Node(s) was/were found, however, exactly two should be present'
    for node in nodes.iterall():
        assert node[0] in [data_uuid, calc_uuid]

    links = get_all_node_links()
    assert len(links) == 1, (
        'Only a single Link (from Calc. to Data) is expected, '
        'instead {} were found (in, out, label, type): {}'.format(len(links), links)
    )
    for from_uuid, to_uuid, found_label, found_type in links:
        assert from_uuid == calc_uuid
        assert to_uuid == data_uuid
        assert found_label == link_label
        assert found_type == LinkType.CREATE.value

    # import data+logic provenance
    import_archive(all_provenance)

    no_of_work = orm.QueryBuilder().append(orm.WorkflowNode).count()
    assert no_of_work == 1, f'{no_of_work} WorkflowNode(s) was/were found, however, exactly one should be present'

    nodes = orm.QueryBuilder().append(orm.Node, project='uuid')
    assert nodes.count() == 3, f'{no_of_work} Node(s) was/were found, however, exactly three should be present'
    for node in nodes.iterall():
        assert node[0] in [data_uuid, calc_uuid, work_uuid]

    links = get_all_node_links()
    assert (
        len(links) == 2
    ), f'Exactly two Links are expected, instead {len(links)} were found (in, out, label, type): {links}'
    assert sorted(links) == sorted(before_links)
