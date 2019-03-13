# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the QueryBuilder."""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import unittest
import warnings

from six.moves import range, zip

from aiida import orm
from aiida.backends import settings
from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType

# pylint: disable=invalid-name,missing-docstring,too-many-lines


class TestQueryBuilder(AiidaTestCase):

    def setUp(self):
        super(TestQueryBuilder, self).setUp()
        self.clean_db()
        self.insert_data()

    def test_ormclass_type_classification(self):
        """
        This tests the classifications of the QueryBuilder
        """
        # pylint: disable=protected-access
        from aiida.common.exceptions import DbContentError

        qb = orm.QueryBuilder()

        # Asserting that improper declarations of the class type raise an error
        with self.assertRaises(DbContentError):
            qb._get_ormclass(None, 'data')
        with self.assertRaises(DbContentError):
            qb._get_ormclass(None, 'data.Data')
        with self.assertRaises(DbContentError):
            qb._get_ormclass(None, '.')

        # Asserting that the query type string and plugin type string are returned:
        for _cls, classifiers in (
                qb._get_ormclass(orm.StructureData, None),
                qb._get_ormclass(None, 'data.structure.StructureData.'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], orm.StructureData._plugin_type_string)  # pylint: disable=no-member

        for _cls, classifiers in (
                qb._get_ormclass(orm.Group, None),
                qb._get_ormclass(None, 'group'),
                qb._get_ormclass(None, 'Group'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'group')

        for _cls, classifiers in (
                qb._get_ormclass(orm.User, None),
                qb._get_ormclass(None, "user"),
                qb._get_ormclass(None, "User"),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'user')

        for _cls, classifiers in (
                qb._get_ormclass(orm.Computer, None),
                qb._get_ormclass(None, 'computer'),
                qb._get_ormclass(None, 'Computer'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], 'computer')

        for _cls, classifiers in (
                qb._get_ormclass(orm.Data, None),
                qb._get_ormclass(None, 'data.Data.'),
        ):
            self.assertEqual(classifiers['ormclass_type_string'], orm.Data._plugin_type_string)  # pylint: disable=no-member

    def test_process_type_classification(self):
        """
        This tests the classifications of the QueryBuilder
        """
        from aiida.engine import WorkChain
        from aiida.plugins import CalculationFactory

        ArithmeticAdd = CalculationFactory('arithmetic.add')

        qb = orm.QueryBuilder()

        # pylint: disable=protected-access

        # When passing a WorkChain class, it should return the type of the corresponding Node
        # including the appropriate filter on the process_type
        _cls, classifiers = qb._get_ormclass(WorkChain, None)
        self.assertEqual(classifiers['ormclass_type_string'], 'process.workflow.workchain.WorkChainNode.')
        self.assertEqual(classifiers['process_type_string'], 'aiida.engine.processes.workchains.workchain.WorkChain')

        # When passing a WorkChainNode, no process_type filter is applied
        _cls, classifiers = qb._get_ormclass(orm.WorkChainNode, None)
        self.assertEqual(classifiers['ormclass_type_string'], 'process.workflow.workchain.WorkChainNode.')
        self.assertEqual(classifiers['process_type_string'], None)

        # Same tests for a calculation
        _cls, classifiers = qb._get_ormclass(ArithmeticAdd, None)
        self.assertEqual(classifiers['ormclass_type_string'], 'process.calculation.calcjob.CalcJobNode.')
        self.assertEqual(classifiers['process_type_string'], 'aiida.calculations:arithmetic.add')

    def test_process_query(self):
        """
        Test querying for a process class.
        """
        from aiida.engine import run, WorkChain, if_, return_, ExitCode
        from aiida.common.warnings import AiidaEntryPointWarning

        class PotentialFailureWorkChain(WorkChain):
            EXIT_STATUS = 1
            EXIT_MESSAGE = 'Well you did ask for it'
            OUTPUT_LABEL = 'optional_output'
            OUTPUT_VALUE = 144

            @classmethod
            def define(cls, spec):
                super(PotentialFailureWorkChain, cls).define(spec)
                spec.input('success', valid_type=orm.Bool)
                spec.input('through_return', valid_type=orm.Bool, default=orm.Bool(False))
                spec.input('through_exit_code', valid_type=orm.Bool, default=orm.Bool(False))
                spec.exit_code(cls.EXIT_STATUS, 'EXIT_STATUS', cls.EXIT_MESSAGE)
                spec.outline(if_(cls.should_return_out_of_outline)(return_(cls.EXIT_STATUS)), cls.failure, cls.success)
                spec.output('optional', required=False)

            def should_return_out_of_outline(self):
                return self.inputs.through_return.value

            def failure(self):
                # pylint: disable=no-else-return

                if self.inputs.success.value is False:
                    # Returning either 0 or ExitCode with non-zero status should terminate the workchain
                    if self.inputs.through_exit_code.value is False:
                        return self.EXIT_STATUS
                    else:
                        return self.exit_codes.EXIT_STATUS  # pylint: disable=no-member
                else:
                    # Returning 0 or ExitCode with zero status should *not* terminate the workchain
                    if self.inputs.through_exit_code.value is False:
                        return 0
                    else:
                        return ExitCode()

            def success(self):
                self.out(self.OUTPUT_LABEL, orm.Int(self.OUTPUT_VALUE))

        class DummyWorkChain(WorkChain):
            pass

        # Run a simple test WorkChain
        _result = run(PotentialFailureWorkChain, success=orm.Bool(True))

        # Query for nodes associated with this type of WorkChain
        qb = orm.QueryBuilder()

        with warnings.catch_warnings(record=True) as w:  # pylint: disable=no-member
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")  # pylint: disable=no-member

            qb.append(PotentialFailureWorkChain)

            # Verify some things
            assert len(w) == 1
            assert issubclass(w[-1].category, AiidaEntryPointWarning)

        # There should be one result of type WorkChainNode
        self.assertEqual(qb.count(), 1)
        self.assertTrue(isinstance(qb.all()[0][0], orm.WorkChainNode))

        # Query for nodes of a different type of WorkChain
        qb = orm.QueryBuilder()

        with warnings.catch_warnings(record=True) as w:  # pylint: disable=no-member
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")  # pylint: disable=no-member

            qb.append(DummyWorkChain)

            # Verify some things
            assert len(w) == 1
            assert issubclass(w[-1].category, AiidaEntryPointWarning)

        # There should be no result
        self.assertEqual(qb.count(), 0)

        # Query for all WorkChain nodes
        qb = orm.QueryBuilder()
        qb.append(WorkChain)

        # There should be one result
        self.assertEqual(qb.count(), 1)

    def test_simple_query_1(self):
        """
        Testing a simple query
        """
        # pylint: disable=too-many-statements

        n1 = orm.Data()
        n1.label = 'node1'
        n1.set_attribute('foo', ['hello', 'goodbye'])
        n1.store()

        n2 = orm.CalculationNode()
        n2.label = 'node2'
        n2.set_attribute('foo', 1)
        n2.store()

        n3 = orm.Data()
        n3.label = 'node3'
        n3.set_attribute('foo', 1.0000)  # Stored as fval
        n3.store()

        n4 = orm.CalculationNode()
        n4.label = 'node4'
        n4.set_attribute('foo', 'bar')
        n4.store()

        n5 = orm.Data()
        n5.label = 'node5'
        n5.set_attribute('foo', None)
        n5.store()

        n2.add_incoming(n1, link_type=LinkType.INPUT_CALC, link_label='link1')
        n3.add_incoming(n2, link_type=LinkType.CREATE, link_label='link2')

        n4.add_incoming(n3, link_type=LinkType.INPUT_CALC, link_label='link3')
        n5.add_incoming(n4, link_type=LinkType.CREATE, link_label='link4')

        qb1 = orm.QueryBuilder()
        qb1.append(orm.Node, filters={'attributes.foo': 1.000})

        self.assertEqual(len(qb1.all()), 2)

        qb2 = orm.QueryBuilder()
        qb2.append(orm.Data)
        self.assertEqual(qb2.count(), 3)

        qb2 = orm.QueryBuilder()
        qb2.append(entity_type='data.Data.')
        self.assertEqual(qb2.count(), 3)

        qb3 = orm.QueryBuilder()
        qb3.append(orm.Node, project='label', tag='node1')
        qb3.append(orm.Node, project='label', tag='node2')
        self.assertEqual(qb3.count(), 4)

        qb4 = orm.QueryBuilder()
        qb4.append(orm.CalculationNode, tag='node1')
        qb4.append(orm.Data, tag='node2')
        self.assertEqual(qb4.count(), 2)

        qb5 = orm.QueryBuilder()
        qb5.append(orm.Data, tag='node1')
        qb5.append(orm.CalculationNode, tag='node2')
        self.assertEqual(qb5.count(), 2)

        qb6 = orm.QueryBuilder()
        qb6.append(orm.Data, tag='node1')
        qb6.append(orm.Data, tag='node2')
        self.assertEqual(qb6.count(), 0)

    def test_simple_query_2(self):
        from datetime import datetime
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        n0 = orm.Data()
        n0.label = 'hello'
        n0.description = ''
        n0.set_attribute('foo', 'bar')

        n1 = orm.CalculationNode()
        n1.label = 'foo'
        n1.description = 'I am FoO'

        n2 = orm.Data()
        n2.label = 'bar'
        n2.description = 'I am BaR'

        n2.add_incoming(n1, link_type=LinkType.CREATE, link_label='random_2')
        n1.add_incoming(n0, link_type=LinkType.INPUT_CALC, link_label='random_1')

        for n in (n0, n1, n2):
            n.store()

        qb1 = orm.QueryBuilder()
        qb1.append(orm.Node, filters={'label': 'hello'})
        self.assertEqual(len(list(qb1.all())), 1)

        qh = {
            'path': [{
                'cls': orm.Node,
                'tag': 'n1'
            }, {
                'cls': orm.Node,
                'tag': 'n2',
                'with_incoming': 'n1'
            }],
            'filters': {
                'n1': {
                    'label': {
                        'ilike': '%foO%'
                    },
                },
                'n2': {
                    'label': {
                        'ilike': 'bar%'
                    },
                }
            },
            'project': {
                'n1': ['id', 'uuid', 'ctime', 'label'],
                'n2': ['id', 'description', 'label'],
            }
        }

        qb2 = orm.QueryBuilder(**qh)

        resdict = qb2.dict()
        self.assertEqual(len(resdict), 1)
        self.assertTrue(isinstance(resdict[0]['n1']['ctime'], datetime))

        res_one = qb2.one()
        self.assertTrue('bar' in res_one)

        qh = {
            'path': [{
                'cls': orm.Node,
                'tag': 'n1'
            }, {
                'cls': orm.Node,
                'tag': 'n2',
                'with_incoming': 'n1'
            }],
            'filters': {
                'n1--n2': {
                    'label': {
                        'like': '%_2'
                    }
                }
            }
        }
        qb = orm.QueryBuilder(**qh)
        self.assertEqual(qb.count(), 1)

        # Test the hashing:
        query1 = qb.get_query()
        qb.add_filter('n2', {'label': 'nonexistentlabel'})
        self.assertEqual(qb.count(), 0)

        with self.assertRaises(NotExistent):
            qb.one()
        with self.assertRaises(MultipleObjectsError):
            orm.QueryBuilder().append(orm.Node).one()

        query2 = qb.get_query()
        query3 = qb.get_query()

        self.assertTrue(id(query1) != id(query2))
        self.assertTrue(id(query2) == id(query3))

    def test_operators_eq_lt_gt(self):
        nodes = [orm.Data() for _ in range(8)]

        nodes[0].set_attribute('fa', 1)
        nodes[1].set_attribute('fa', 1.0)
        nodes[2].set_attribute('fa', 1.01)
        nodes[3].set_attribute('fa', 1.02)
        nodes[4].set_attribute('fa', 1.03)
        nodes[5].set_attribute('fa', 1.04)
        nodes[6].set_attribute('fa', 1.05)
        nodes[7].set_attribute('fa', 1.06)

        for n in nodes:
            n.store()

        self.assertEqual(orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'<': 1}}).count(), 0)
        self.assertEqual(orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'==': 1}}).count(), 2)
        self.assertEqual(orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'<': 1.02}}).count(), 3)
        self.assertEqual(orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'<=': 1.02}}).count(), 4)
        self.assertEqual(orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'>': 1.02}}).count(), 4)
        self.assertEqual(orm.QueryBuilder().append(orm.Node, filters={'attributes.fa': {'>=': 1.02}}).count(), 5)

    def test_subclassing(self):
        s = orm.StructureData()
        s.set_attribute('cat', 'miau')
        s.store()

        d = orm.Data()
        d.set_attribute('cat', 'miau')
        d.store()

        p = orm.Dict(dict=dict(cat='miau'))
        p.store()

        # Now when asking for a node with attr.cat==miau, I want 3 esults:
        qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 3)

        qb = orm.QueryBuilder().append(orm.Data, filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 3)

        # If I'm asking for the specific lowest subclass, I want one result
        for cls in (orm.StructureData, orm.Dict):
            qb = orm.QueryBuilder().append(cls, filters={'attributes.cat': 'miau'})
            self.assertEqual(qb.count(), 1)

        # Now I am not allow the subclassing, which should give 1 result for each
        for cls, count in ((orm.StructureData, 1), (orm.Dict, 1), (orm.Data, 1), (orm.Node, 0)):
            qb = orm.QueryBuilder().append(cls, filters={'attributes.cat': 'miau'}, subclassing=False)
            self.assertEqual(qb.count(), count)

        # Now I am testing the subclassing with tuples:
        qb = orm.QueryBuilder().append(cls=(orm.StructureData, orm.Dict), filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 2)
        qb = orm.QueryBuilder().append(
            entity_type=('data.structure.StructureData.', 'data.dict.Dict.'), filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 2)
        qb = orm.QueryBuilder().append(
            cls=(orm.StructureData, orm.Dict), filters={'attributes.cat': 'miau'}, subclassing=False)
        self.assertEqual(qb.count(), 2)
        qb = orm.QueryBuilder().append(
            cls=(orm.StructureData, orm.Data),
            filters={'attributes.cat': 'miau'},
        )
        self.assertEqual(qb.count(), 3)
        qb = orm.QueryBuilder().append(
            entity_type=('data.structure.StructureData.', 'data.dict.Dict.'),
            filters={'attributes.cat': 'miau'},
            subclassing=False)
        self.assertEqual(qb.count(), 2)
        qb = orm.QueryBuilder().append(
            entity_type=('data.structure.StructureData.', 'data.Data.'),
            filters={'attributes.cat': 'miau'},
            subclassing=False)
        self.assertEqual(qb.count(), 2)

    def test_list_behavior(self):
        for _i in range(4):
            orm.Data().store()

        self.assertEqual(len(orm.QueryBuilder().append(orm.Node).all()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node, project='*').all()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).all()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node, project=['id']).all()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node).dict()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node, project='*').dict()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).dict()), 4)
        self.assertEqual(len(orm.QueryBuilder().append(orm.Node, project=['id']).dict()), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node).iterall())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node, project='*').iterall())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).iterall())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node, project=['id']).iterall())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node).iterdict())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node, project='*').iterdict())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node, project=['*', 'id']).iterdict())), 4)
        self.assertEqual(len(list(orm.QueryBuilder().append(orm.Node, project=['id']).iterdict())), 4)

    def test_append_validation(self):
        from aiida.common.exceptions import InputValidationError

        # So here I am giving two times the same tag
        with self.assertRaises(InputValidationError):
            orm.QueryBuilder().append(orm.StructureData, tag='n').append(orm.StructureData, tag='n')
        # here I am giving a wrong filter specifications
        with self.assertRaises(InputValidationError):
            orm.QueryBuilder().append(orm.StructureData, filters=['jajjsd'])
        # here I am giving a nonsensical projection:
        with self.assertRaises(InputValidationError):
            orm.QueryBuilder().append(orm.StructureData, project=True)

        # here I am giving a nonsensical projection for the edge:
        with self.assertRaises(InputValidationError):
            orm.QueryBuilder().append(orm.ProcessNode).append(orm.StructureData, edge_tag='t').add_projection('t', True)
        # Giving a nonsensical limit
        with self.assertRaises(InputValidationError):
            orm.QueryBuilder().append(orm.ProcessNode).limit(2.3)
        # Giving a nonsensical offset
        with self.assertRaises(InputValidationError):
            orm.QueryBuilder(offset=2.3)

        # So, I mess up one append, I want the QueryBuilder to clean it!
        with self.assertRaises(InputValidationError):
            qb = orm.QueryBuilder()
            # This also checks if we correctly raise for wrong keywords
            qb.append(orm.StructureData, tag='s', randomkeyword={})

        # Now I'm checking whether this keyword appears anywhere in the internal dictionaries:
        # pylint: disable=protected-access
        self.assertTrue('s' not in qb._projections)
        self.assertTrue('s' not in qb._filters)
        self.assertTrue('s' not in qb._tag_to_alias_map)
        self.assertTrue(len(qb._path) == 0)
        self.assertTrue(orm.StructureData not in qb._cls_to_tag_map)
        # So this should work now:
        qb.append(orm.StructureData, tag='s').limit(2).dict()

    def test_tags(self):
        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='n1')
        qb.append(orm.Node, tag='n2', edge_tag='e1', with_incoming='n1')
        qb.append(orm.Node, tag='n3', edge_tag='e2', with_incoming='n2')
        qb.append(orm.Computer, with_node='n3', tag='c1', edge_tag='nonsense')
        self.assertEqual(qb.get_used_tags(), ['n1', 'n2', 'e1', 'n3', 'e2', 'c1', 'nonsense'])

        # Now I am testing the default tags,
        qb = orm.QueryBuilder().append(orm.StructureData).append(orm.ProcessNode).append(orm.StructureData).append(
            orm.Dict, with_outgoing=orm.ProcessNode)
        self.assertEqual(qb.get_used_tags(), [
            'StructureData_1', 'ProcessNode_1', 'StructureData_1--ProcessNode_1', 'StructureData_2',
            'ProcessNode_1--StructureData_2', 'Dict_1', 'ProcessNode_1--Dict_1'
        ])
        self.assertEqual(
            qb.get_used_tags(edges=False), [
                'StructureData_1',
                'ProcessNode_1',
                'StructureData_2',
                'Dict_1',
            ])
        self.assertEqual(
            qb.get_used_tags(vertices=False),
            ['StructureData_1--ProcessNode_1', 'ProcessNode_1--StructureData_2', 'ProcessNode_1--Dict_1'])
        self.assertEqual(
            qb.get_used_tags(edges=False), [
                'StructureData_1',
                'ProcessNode_1',
                'StructureData_2',
                'Dict_1',
            ])
        self.assertEqual(
            qb.get_used_tags(vertices=False),
            ['StructureData_1--ProcessNode_1', 'ProcessNode_1--StructureData_2', 'ProcessNode_1--Dict_1'])


class TestQueryHelp(AiidaTestCase):

    def test_queryhelp(self):
        """
        Here I test the queryhelp by seeing whether results are the same as using the append method.
        I also check passing of tuples.
        """
        g = orm.Group(label='helloworld').store()
        for cls in (orm.StructureData, orm.Dict, orm.Data):
            obj = cls()
            obj.set_attribute('foo-qh2', 'bar')
            obj.store()
            g.add_nodes(obj)

        for cls, expected_count, subclassing in (
            (orm.StructureData, 1, True),
            (orm.Dict, 1, True),
            (orm.Data, 3, True),
            (orm.Data, 1, False),
            ((orm.Dict, orm.StructureData), 2, True),
            ((orm.Dict, orm.StructureData), 2, False),
            ((orm.Dict, orm.Data), 2, False),
            ((orm.Dict, orm.Data), 3, True),
            ((orm.Dict, orm.Data, orm.StructureData), 3, False),
        ):
            qb = orm.QueryBuilder()
            qb.append(cls, filters={'attributes.foo-qh2': 'bar'}, subclassing=subclassing, project='uuid')
            self.assertEqual(qb.count(), expected_count)

            qh = qb.get_json_compatible_queryhelp()
            qb_new = orm.QueryBuilder(**qh)
            self.assertEqual(qb_new.count(), expected_count)
            self.assertEqual(sorted([uuid for uuid, in qb.all()]), sorted([uuid for uuid, in qb_new.all()]))

        qb = orm.QueryBuilder().append(orm.Group, filters={'label': 'helloworld'})
        self.assertEqual(qb.count(), 1)

        qb = orm.QueryBuilder().append((orm.Group,), filters={'label': 'helloworld'})
        self.assertEqual(qb.count(), 1)

        qb = orm.QueryBuilder().append(orm.Computer,)
        self.assertEqual(qb.count(), 1)

        qb = orm.QueryBuilder().append(cls=(orm.Computer,))
        self.assertEqual(qb.count(), 1)


class TestQueryBuilderCornerCases(AiidaTestCase):
    """
    In this class corner cases of QueryBuilder are added.
    """

    def test_computer_json(self):  # pylint: disable=no-self-use
        """
        In this test we check the correct behavior of QueryBuilder when
        retrieving the _metadata and the transport_params with no content.
        Note that they are in JSON format in both backends. Forcing the
        decoding of a None value leads to an exception (this was the case
        under Django).
        """
        n1 = orm.CalculationNode()
        n1.label = 'node2'
        n1.set_attribute('foo', 1)
        n1.store()

        # Checking the correct retrieval of transport_params which is
        # a JSON field (in both backends).
        qb = orm.QueryBuilder()
        qb.append(orm.CalculationNode, project=['id'], tag='calc')
        qb.append(orm.Computer, project=['id', 'transport_params'], outerjoin=True, with_node='calc')
        qb.all()

        # Checking the correct retrieval of _metadata which is
        # a JSON field (in both backends).
        qb = orm.QueryBuilder()
        qb.append(orm.CalculationNode, project=['id'], tag='calc')
        qb.append(orm.Computer, project=['id', '_metadata'], outerjoin=True, with_node='calc')
        qb.all()


class TestAttributes(AiidaTestCase):

    def test_attribute_existence(self):
        # I'm storing a value under key whatever:
        val = 1.
        res_uuids = set()
        n1 = orm.Data()
        n1.set_attribute("whatever", 3.)
        n1.set_attribute("test_case", "test_attribute_existence")
        n1.store()

        # I want all the nodes where whatever is smaller than 1. or there is no such value:

        qb = orm.QueryBuilder()
        qb.append(
            orm.Data,
            filters={
                'or': [{
                    'attributes': {
                        '!has_key': 'whatever'
                    }
                }, {
                    'attributes.whatever': {
                        '<': val
                    }
                }],
            },
            project='uuid')
        res_query = {str(_[0]) for _ in qb.all()}
        self.assertEqual(res_query, res_uuids)

    def test_attribute_type(self):
        key = 'value_test_attr_type'
        n_int, n_float, n_str, n_str2, n_bool, n_arr = [orm.Data() for _ in range(6)]
        n_int.set_attribute(key, 1)
        n_float.set_attribute(key, 1.0)
        n_bool.set_attribute(key, True)
        n_str.set_attribute(key, '1')
        n_str2.set_attribute(key, 'one')
        n_arr.set_attribute(key, [4, 3, 5])

        for n in (n_str2, n_str, n_int, n_float, n_bool, n_arr):
            n.store()

        # Here I am testing which values contain a number 1.
        # Both 1 and 1.0 are legitimate values if ask for either 1 or 1.0
        for val in (1.0, 1):
            qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): val}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_float.uuid, n_int.uuid)))
            qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): {'>': 0.5}}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_float.uuid, n_int.uuid)))
            qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): {'<': 1.5}}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_float.uuid, n_int.uuid)))
        # Now I am testing the boolean value:
        qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): True}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_bool.uuid,)))

        qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): {'like': '%n%'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str2.uuid,)))
        qb = orm.QueryBuilder().append(
            orm.Node, filters={'attributes.{}'.format(key): {
                                   'ilike': 'On%'
                               }}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str2.uuid,)))
        qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): {'like': '1'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str.uuid,)))
        qb = orm.QueryBuilder().append(orm.Node, filters={'attributes.{}'.format(key): {'==': '1'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str.uuid,)))
        if settings.BACKEND == u'sqlalchemy':
            # I can't query the length of an array with Django,
            # so I exclude. Not the nicest way, But I would like to keep this piece
            # of code because of the initialization part, that would need to be
            # duplicated or wrapped otherwise.
            qb = orm.QueryBuilder().append(
                orm.Node, filters={'attributes.{}'.format(key): {
                                       'of_length': 3
                                   }}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_arr.uuid,)))


class QueryBuilderDateTimeAttribute(AiidaTestCase):

    @unittest.skipIf(settings.BACKEND == u'sqlalchemy', "SQLA doesn't have full datetime support in attributes")
    def test_date(self):
        from aiida.common import timezone
        from datetime import timedelta
        n = orm.Data()
        now = timezone.now()
        n.set_attribute('now', now)
        n.store()

        qb = orm.QueryBuilder().append(
            orm.Node,
            filters={
                'attributes.now': {
                    "and": [
                        {
                            ">": now - timedelta(seconds=1)
                        },
                        {
                            "<": now + timedelta(seconds=1)
                        },
                    ]
                }
            })
        self.assertEqual(qb.count(), 1)


class QueryBuilderLimitOffsetsTest(AiidaTestCase):

    def test_ordering_limits_offsets_of_results_general(self):
        # Creating 10 nodes with an attribute that can be ordered
        for i in range(10):
            n = orm.Data()
            n.set_attribute('foo', i)
            n.store()

        qb = orm.QueryBuilder().append(orm.Node, project='attributes.foo').order_by({orm.Node: 'ctime'})

        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(10)))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(5, 10)))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(5, 8)))

        # Specifying the order  explicitly the order:
        qb = orm.QueryBuilder().append(
            orm.Node, project='attributes.foo').order_by({orm.Node: {
                'ctime': {
                    'order': 'asc'
                }
            }})

        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(10)))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(5, 10)))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(5, 8)))

        # Reversing the order:
        qb = orm.QueryBuilder().append(
            orm.Node, project='attributes.foo').order_by({orm.Node: {
                'ctime': {
                    'order': 'desc'
                }
            }})

        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(9, -1, -1)))

        # Now applying an offset:
        qb.offset(5)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(4, -1, -1)))

        # Now also applying a limit:
        qb.limit(3)
        res = next(zip(*qb.all()))
        self.assertEqual(res, tuple(range(4, 1, -1)))


class QueryBuilderJoinsTests(AiidaTestCase):

    def test_joins1(self):
        # Creating n1, who will be a parent:
        parent = orm.Data()
        parent.label = 'mother'

        good_child = orm.CalculationNode()
        good_child.label = 'good_child'
        good_child.set_attribute('is_good', True)

        bad_child = orm.CalculationNode()
        bad_child.label = 'bad_child'
        bad_child.set_attribute('is_good', False)

        unrelated = orm.CalculationNode()
        unrelated.label = 'unrelated'

        for n in (good_child, bad_child, parent, unrelated):
            n.store()

        good_child.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='parent')
        bad_child.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='parent')

        # Using a standard inner join
        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='parent')
        qb.append(orm.Node, tag='children', project='label', filters={'attributes.is_good': True})
        self.assertEqual(qb.count(), 1)

        qb = orm.QueryBuilder()
        qb.append(orm.Node, tag='parent')
        qb.append(orm.Node, tag='children', outerjoin=True, project='label', filters={'attributes.is_good': True})
        self.assertEqual(qb.count(), 1)

    def test_joins2(self):
        # Creating n1, who will be a parent:

        students = [orm.Data() for i in range(10)]
        advisors = [orm.CalculationNode() for i in range(3)]
        for i, a in enumerate(advisors):
            a.label = 'advisor {}'.format(i)
            a.set_attribute('advisor_id', i)

        for n in advisors + students:
            n.store()

        # advisor 0 get student 0, 1
        for i in (0, 1):
            students[i].add_incoming(advisors[0], link_type=LinkType.CREATE, link_label='is_advisor_{}'.format(i))

        # advisor 1 get student 3, 4
        for i in (3, 4):
            students[i].add_incoming(advisors[1], link_type=LinkType.CREATE, link_label='is_advisor_{}'.format(i))

        # advisor 2 get student 5, 6, 7
        for i in (5, 6, 7):
            students[i].add_incoming(advisors[2], link_type=LinkType.CREATE, link_label='is_advisor_{}'.format(i))

        # let's add a differnt relationship than advisor:
        students[9].add_incoming(advisors[2], link_type=LinkType.CREATE, link_label='lover')

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node).append(
                orm.Node, edge_filters={
                    'label': {
                        'like': 'is\\_advisor\\_%'
                    }
                }, tag='student').count(), 7)

        for adv_id, number_students in zip(list(range(3)), (2, 2, 3)):
            self.assertEqual(
                orm.QueryBuilder().append(orm.Node, filters={
                    'attributes.advisor_id': adv_id
                }).append(orm.Node, edge_filters={
                    'label': {
                        'like': 'is\\_advisor\\_%'
                    }
                }, tag='student').count(), number_students)

    def test_joins3_user_group(self):
        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email).store()

        # Create a group that belongs to that user
        group = orm.Group(label="node_group")
        group.user = user
        group.store()

        # Search for the group of the user
        qb = orm.QueryBuilder()
        qb.append(orm.User, tag='user', filters={'id': {'==': user.id}})
        qb.append(orm.Group, with_user='user', filters={'id': {'==': group.id}})
        self.assertEqual(qb.count(), 1, "The expected group that belongs to " "the selected user was not found.")

        # Search for the user that owns a group
        qb = orm.QueryBuilder()
        qb.append(orm.Group, tag='group', filters={'id': {'==': group.id}})
        qb.append(orm.User, with_group='group', filters={'id': {'==': user.id}})

        self.assertEqual(qb.count(), 1, "The expected user that owns the " "selected group was not found.")


class QueryBuilderPath(AiidaTestCase):

    def test_query_path(self):
        # pylint: disable=too-many-statements

        q = self.backend.query_manager
        n1 = orm.Data()
        n1.label = 'n1'
        n1.store()
        n2 = orm.CalculationNode()
        n2.label = 'n2'
        n2.store()
        n3 = orm.Data()
        n3.label = 'n3'
        n3.store()
        n4 = orm.Data()
        n4.label = 'n4'
        n4.store()
        n5 = orm.CalculationNode()
        n5.label = 'n5'
        n5.store()
        n6 = orm.Data()
        n6.label = 'n6'
        n6.store()
        n7 = orm.CalculationNode()
        n7.label = 'n7'
        n7.store()
        n8 = orm.Data()
        n8.label = 'n8'
        n8.store()
        n9 = orm.Data()
        n9.label = 'n9'
        n9.store()

        # I create a strange graph, inserting links in a order
        # such that I often have to create the transitive closure
        # between two graphs
        n3.add_incoming(n2, link_type=LinkType.CREATE, link_label='link1')
        n2.add_incoming(n1, link_type=LinkType.INPUT_CALC, link_label='link2')
        n5.add_incoming(n3, link_type=LinkType.INPUT_CALC, link_label='link3')
        n5.add_incoming(n4, link_type=LinkType.INPUT_CALC, link_label='link4')
        n4.add_incoming(n2, link_type=LinkType.CREATE, link_label='link5')
        n7.add_incoming(n6, link_type=LinkType.INPUT_CALC, link_label='link6')
        n8.add_incoming(n7, link_type=LinkType.CREATE, link_label='link7')

        # There are no parents to n9, checking that
        self.assertEqual(set([]), set(q.get_all_parents([n9.pk])))
        # There is one parent to n6
        self.assertEqual({(_,) for _ in (n6.pk,)}, {tuple(_) for _ in q.get_all_parents([n7.pk])})
        # There are several parents to n4
        self.assertEqual({(_.pk,) for _ in (n1, n2)}, {tuple(_) for _ in q.get_all_parents([n4.pk])})
        # There are several parents to n5
        self.assertEqual({(_.pk,) for _ in (n1, n2, n3, n4)}, {tuple(_) for _ in q.get_all_parents([n5.pk])})

        # Yet, no links from 1 to 8
        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n1.pk
            }, tag='anc').append(orm.Node, with_ancestors='anc', filters={
                'id': n8.pk
            }).count(), 0)

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(orm.Node, with_descendants='desc', filters={
                'id': n1.pk
            }).count(), 0)

        n6.add_incoming(n5, link_type=LinkType.CREATE, link_label='link1')
        # Yet, now 2 links from 1 to 8
        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n1.pk
            }, tag='anc').append(orm.Node, with_ancestors='anc', filters={
                'id': n8.pk
            }).count(), 2)

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(orm.Node, with_descendants='desc', filters={
                'id': n1.pk
            }).count(), 2)

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(
                orm.Node,
                with_descendants='desc',
                filters={
                    'id': n1.pk
                },
                edge_filters={
                    'depth': {
                        '<': 6
                    }
                },
            ).count(), 2)
        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(
                orm.Node,
                with_descendants='desc',
                filters={
                    'id': n1.pk
                },
                edge_filters={
                    'depth': 5
                },
            ).count(), 2)
        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(
                orm.Node,
                with_descendants='desc',
                filters={
                    'id': n1.pk
                },
                edge_filters={
                    'depth': {
                        '<': 5
                    }
                },
            ).count(), 0)

        # TODO write a query that can filter certain paths by traversed ID # pylint: disable=fixme
        qb = orm.QueryBuilder().append(
            orm.Node,
            filters={
                'id': n8.pk
            },
            tag='desc',
        ).append(
            orm.Node, with_descendants='desc', edge_project='path', filters={'id': n1.pk})
        queried_path_set = {frozenset(p) for p, in qb.all()}

        paths_there_should_be = {
            frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
            frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk])
        }

        self.assertTrue(queried_path_set == paths_there_should_be)

        qb = orm.QueryBuilder().append(
            orm.Node, filters={
                'id': n1.pk
            }, tag='anc').append(
                orm.Node, with_ancestors='anc', filters={'id': n8.pk}, edge_project='path')

        self.assertEqual({frozenset(p) for p, in qb.all()}, {
            frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
            frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk])
        })

        n7.add_incoming(n9, link_type=LinkType.INPUT_CALC, link_label='link0')
        # Still two links...

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n1.pk
            }, tag='anc').append(orm.Node, with_ancestors='anc', filters={
                'id': n8.pk
            }).count(), 2)

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(orm.Node, with_descendants='desc', filters={
                'id': n1.pk
            }).count(), 2)
        n9.add_incoming(n5, link_type=LinkType.CREATE, link_label='link6')
        # And now there should be 4 nodes

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n1.pk
            }, tag='anc').append(orm.Node, with_ancestors='anc', filters={
                'id': n8.pk
            }).count(), 4)

        self.assertEqual(
            orm.QueryBuilder().append(orm.Node, filters={
                'id': n8.pk
            }, tag='desc').append(orm.Node, with_descendants='desc', filters={
                'id': n1.pk
            }).count(), 4)

        qb = orm.QueryBuilder().append(
            orm.Node, filters={
                'id': n1.pk
            }, tag='anc').append(
                orm.Node, with_ancestors='anc', filters={'id': n8.pk}, edge_tag='edge')
        qb.add_projection('edge', 'depth')
        self.assertTrue(set(next(zip(*qb.all()))), set([5, 6]))
        qb.add_filter('edge', {'depth': 5})
        self.assertTrue(set(next(zip(*qb.all()))), set([5]))


class TestConsistency(AiidaTestCase):

    def test_create_node_and_query(self):
        """
        Testing whether creating nodes within a iterall iteration changes the results.
        """
        for _i in range(100):
            n = orm.Data()
            n.store()

        for idx, _item in enumerate(orm.QueryBuilder().append(orm.Node, project=['id',
                                                                                 'label']).iterall(batch_size=10)):
            if idx % 10 == 10:
                n = orm.Data()
                n.store()
        self.assertEqual(idx, 99)  # pylint: disable=undefined-loop-variable
        self.assertTrue(len(orm.QueryBuilder().append(orm.Node, project=['id', 'label']).all(batch_size=10)) > 99)

    def test_len_results(self):
        """
        Test whether the len of results matches the count returned.
        See also https://github.com/aiidateam/aiida_core/issues/1600
        SQLAlchemy has a deduplication strategy that leads to strange behavior, tested against here
        """
        parent = orm.CalculationNode().store()
        # adding 5 links going out:
        for inode in range(5):
            output_node = orm.Data().store()
            output_node.add_incoming(parent, link_type=LinkType.CREATE, link_label='link-{}'.format(inode))
        for projection in ('id', '*'):
            qb = orm.QueryBuilder()
            qb.append(orm.CalculationNode, filters={'id': parent.id}, tag='parent', project=projection)
            qb.append(orm.Data, with_incoming='parent')
            self.assertEqual(len(qb.all()), qb.count())


class TestManager(AiidaTestCase):

    def test_statistics(self):
        """
        Test if the statistics query works properly.

        I try to implement it in a way that does not depend on the past state.
        """
        from collections import defaultdict

        # pylint: disable=protected-access

        def store_and_add(n, statistics):
            n.store()
            statistics['total'] += 1
            statistics['types'][n._plugin_type_string] += 1  # pylint: disable=no-member
            statistics['ctime_by_day'][n.ctime.strftime('%Y-%m-%d')] += 1

        qmanager = self.backend.query_manager
        current_db_statistics = qmanager.get_creation_statistics()
        types = defaultdict(int)
        types.update(current_db_statistics['types'])
        ctime_by_day = defaultdict(int)
        ctime_by_day.update(current_db_statistics['ctime_by_day'])

        expected_db_statistics = {'total': current_db_statistics['total'], 'types': types, 'ctime_by_day': ctime_by_day}

        store_and_add(orm.Data(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.CalculationNode(), expected_db_statistics)

        new_db_statistics = qmanager.get_creation_statistics()
        # I only check a few fields
        new_db_statistics = {k: v for k, v in new_db_statistics.items() if k in expected_db_statistics}

        expected_db_statistics = {
            k: dict(v) if isinstance(v, defaultdict) else v for k, v in expected_db_statistics.items()
        }

        self.assertEqual(new_db_statistics, expected_db_statistics)

    def test_statistics_default_class(self):
        """
        Test if the statistics query works properly.

        I try to implement it in a way that does not depend on the past state.
        """
        from collections import defaultdict

        def store_and_add(n, statistics):
            n.store()
            statistics['total'] += 1
            statistics['types'][n._plugin_type_string] += 1  # pylint: disable=no-member,protected-access
            statistics['ctime_by_day'][n.ctime.strftime('%Y-%m-%d')] += 1

        current_db_statistics = self.backend.query_manager.get_creation_statistics()
        types = defaultdict(int)
        types.update(current_db_statistics['types'])
        ctime_by_day = defaultdict(int)
        ctime_by_day.update(current_db_statistics['ctime_by_day'])

        expected_db_statistics = {'total': current_db_statistics['total'], 'types': types, 'ctime_by_day': ctime_by_day}

        store_and_add(orm.Data(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.Dict(), expected_db_statistics)
        store_and_add(orm.CalculationNode(), expected_db_statistics)

        new_db_statistics = self.backend.query_manager.get_creation_statistics()
        # I only check a few fields
        new_db_statistics = {k: v for k, v in new_db_statistics.items() if k in expected_db_statistics}

        expected_db_statistics = {
            k: dict(v) if isinstance(v, defaultdict) else v for k, v in expected_db_statistics.items()
        }

        self.assertEqual(new_db_statistics, expected_db_statistics)
