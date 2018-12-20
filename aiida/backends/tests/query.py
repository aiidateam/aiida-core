# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
import unittest

from six.moves import range, zip

from aiida.backends.testbase import AiidaTestCase
import aiida.backends.settings as settings
from aiida.common.links import LinkType
from aiida.orm import Node, Data
from aiida.orm.node.process.calculation import CalculationNode

class TestQueryBuilder(AiidaTestCase):

    def setUp(self):
        super(TestQueryBuilder, self).setUp()
        self.clean_db()
        self.insert_data()

    def test_classification(self):
        """
        This tests the classifications of the QueryBuilder
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.data.structure import StructureData
        from aiida.orm import Group, User, Node, Computer, Data
        from aiida.common.exceptions import InputValidationError

        qb = QueryBuilder()

        # Asserting that improper declarations of the class type raise an error
        with self.assertRaises(InputValidationError):
            qb._get_ormclass(None, 'data')
        with self.assertRaises(InputValidationError):
            qb._get_ormclass(None, 'data.Data')
        with self.assertRaises(InputValidationError):
            qb._get_ormclass(None, '.')

        # Asserting that the query type string and plugin type string are returned:
        for cls, clstype, query_type_string in (
                qb._get_ormclass(StructureData, None),
                qb._get_ormclass(None, 'data.structure.StructureData.'),
        ):
            self.assertEqual(clstype,
                             StructureData._plugin_type_string)
            self.assertEqual(query_type_string,
                             StructureData._query_type_string)

        for cls, clstype, query_type_string in (
                qb._get_ormclass(Node, None),
                qb._get_ormclass(None, '')
        ):
            self.assertEqual(clstype, Node._plugin_type_string)
            self.assertEqual(query_type_string, Node._query_type_string)

        for cls, clstype, query_type_string in (
                qb._get_ormclass(Group, None),
                qb._get_ormclass(None, 'group'),
                qb._get_ormclass(None, 'Group'),
        ):
            self.assertEqual(clstype, 'group')
            self.assertEqual(query_type_string, None)

        for cls, clstype, query_type_string in (
                qb._get_ormclass(User, None),
                qb._get_ormclass(None, "user"),
                qb._get_ormclass(None, "User"),
        ):
            self.assertEqual(clstype, 'user')
            self.assertEqual(query_type_string, None)

        for cls, clstype, query_type_string in (
                qb._get_ormclass(Computer, None),
                qb._get_ormclass(None, 'computer'),
                qb._get_ormclass(None, 'Computer'),
        ):
            self.assertEqual(clstype, 'computer')
            self.assertEqual(query_type_string, None)

        for cls, clstype, query_type_string in (
                qb._get_ormclass(Data, None),
                qb._get_ormclass(None, 'data.Data.'),
        ):
            self.assertEqual(clstype, Data._plugin_type_string)
            self.assertEqual(query_type_string, Data._query_type_string)

    def test_simple_query_1(self):
        """
        Testing a simple query
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node, Data
        from aiida.orm.node.process import CalculationNode
        from datetime import datetime
        from aiida.common.links import LinkType

        n1 = Data()
        n1.label = 'node1'
        n1._set_attr('foo', ['hello', 'goodbye'])
        n1.store()

        n2 = CalculationNode()
        n2.label = 'node2'
        n2._set_attr('foo', 1)
        n2.store()

        n3 = Data()
        n3.label = 'node3'
        n3._set_attr('foo', 1.0000)  # Stored as fval
        n3.store()

        n4 = CalculationNode()
        n4.label = 'node4'
        n4._set_attr('foo', 'bar')
        n4.store()

        n5 = Data()
        n5.label = 'node5'
        n5._set_attr('foo', None)
        n5.store()

        n2.add_incoming(n1, link_type=LinkType.INPUT_CALC, link_label='link1')
        n3.add_incoming(n2, link_type=LinkType.CREATE, link_label='link2')

        n4.add_incoming(n3, link_type=LinkType.INPUT_CALC, link_label='link3')
        n5.add_incoming(n4, link_type=LinkType.CREATE, link_label='link4')

        qb1 = QueryBuilder()
        qb1.append(Node, filters={'attributes.foo': 1.000})

        self.assertEqual(len(qb1.all()), 2)

        qb2 = QueryBuilder()
        qb2.append(Data)
        self.assertEqual(qb2.count(), 3)

        qb2 = QueryBuilder()
        qb2.append(type='data.Data.')
        self.assertEqual(qb2.count(), 3)

        qb3 = QueryBuilder()
        qb3.append(Node, project='label', tag='node1')
        qb3.append(Node, project='label', tag='node2')
        self.assertEqual(qb3.count(), 4)

        qb4 = QueryBuilder()
        qb4.append(CalculationNode, tag='node1')
        qb4.append(Data, tag='node2')
        self.assertEqual(qb4.count(), 2)

        qb5 = QueryBuilder()
        qb5.append(Data, tag='node1')
        qb5.append(CalculationNode, tag='node2')
        self.assertEqual(qb5.count(), 2)

        qb6 = QueryBuilder()
        qb6.append(Data, tag='node1')
        qb6.append(Data, tag='node2')
        self.assertEqual(qb6.count(), 0)

    def test_simple_query_2(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node, Data
        from aiida.orm.node.process.calculation import CalculationNode
        from datetime import datetime
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        n0 = Data()
        n0.label = 'hello'
        n0.description = ''
        n0._set_attr('foo', 'bar')

        n1 = CalculationNode()
        n1.label = 'foo'
        n1.description = 'I am FoO'

        n2 = Data()
        n2.label = 'bar'
        n2.description = 'I am BaR'

        n2.add_incoming(n1, link_type=LinkType.CREATE, link_label='random_2')
        n1.add_incoming(n0, link_type=LinkType.INPUT_CALC, link_label='random_1')

        for n in (n0, n1, n2):
            n.store()

        qb1 = QueryBuilder()
        qb1.append(Node, filters={'label': 'hello'})
        self.assertEqual(len(list(qb1.all())), 1)

        qh = {
            'path': [
                {
                    'cls': Node,
                    'tag': 'n1'
                },
                {
                    'cls': Node,
                    'tag': 'n2',
                    'with_incoming': 'n1'
                }
            ],
            'filters': {
                'n1': {
                    'label': {'ilike': '%foO%'},
                },
                'n2': {
                    'label': {'ilike': 'bar%'},
                }
            },
            'project': {
                'n1': ['id', 'uuid', 'ctime', 'label'],
                'n2': ['id', 'description', 'label'],
            }
        }

        qb2 = QueryBuilder(**qh)

        resdict = qb2.dict()
        self.assertEqual(len(resdict), 1)
        self.assertTrue(isinstance(resdict[0]['n1']['ctime'], datetime))

        res_one = qb2.one()
        self.assertTrue('bar' in res_one)

        qh = {
            'path': [
                {
                    'cls': Node,
                    'tag': 'n1'
                },
                {
                    'cls': Node,
                    'tag': 'n2',
                    'with_incoming': 'n1'
                }
            ],
            'filters': {
                'n1--n2': {'label': {'like': '%_2'}}
            }
        }
        qb = QueryBuilder(**qh)
        self.assertEqual(qb.count(), 1)

        # Test the hashing:
        query1 = qb.get_query()
        qb.add_filter('n2', {'label': 'nonexistentlabel'})
        self.assertEqual(qb.count(), 0)

        with self.assertRaises(NotExistent):
            qb.one()
        with self.assertRaises(MultipleObjectsError):
            QueryBuilder().append(Node).one()

        query2 = qb.get_query()
        query3 = qb.get_query()

        self.assertTrue(id(query1) != id(query2))
        self.assertTrue(id(query2) == id(query3))

    def test_operators_eq_lt_gt(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node

        nodes = [Data() for _ in range(8)]

        nodes[0]._set_attr('fa', 1)
        nodes[1]._set_attr('fa', 1.0)
        nodes[2]._set_attr('fa', 1.01)
        nodes[3]._set_attr('fa', 1.02)
        nodes[4]._set_attr('fa', 1.03)
        nodes[5]._set_attr('fa', 1.04)
        nodes[6]._set_attr('fa', 1.05)
        nodes[7]._set_attr('fa', 1.06)

        [n.store() for n in nodes]

        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa': {'<': 1}}).count(), 0)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa': {'==': 1}}).count(), 2)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa': {'<': 1.02}}).count(), 3)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa': {'<=': 1.02}}).count(), 4)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa': {'>': 1.02}}).count(), 4)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa': {'>=': 1.02}}).count(), 5)

    def test_subclassing(self):
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm import Node, Data
        from aiida.orm.querybuilder import QueryBuilder
        s = StructureData()
        s._set_attr('cat', 'miau')
        s.store()

        d = Data()
        d._set_attr('cat', 'miau')
        d.store()

        p = ParameterData(dict=dict(cat='miau'))
        p.store()

        # Now when asking for a node with attr.cat==miau, I want 3 esults:
        qb = QueryBuilder().append(Node, filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 3)

        qb = QueryBuilder().append(Data, filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 3)

        # If I'm asking for the specific lowest subclass, I want one result
        for cls in (StructureData, ParameterData):
            qb = QueryBuilder().append(cls, filters={'attributes.cat': 'miau'})
            self.assertEqual(qb.count(), 1)

        # Now I am not allow the subclassing, which should give 1 result for each
        for cls, count in (
            (StructureData, 1),
            (ParameterData, 1),
            (Data, 1),
            (Node, 0)):
            qb = QueryBuilder().append(cls, filters={'attributes.cat': 'miau'}, subclassing=False)
            self.assertEqual(qb.count(), count)

        # Now I am testing the subclassing with tuples:
        qb = QueryBuilder().append(cls=(StructureData, ParameterData), filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 2)
        qb = QueryBuilder().append(type=('data.structure.StructureData.', 'data.parameter.ParameterData.'),
                                   filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 2)
        qb = QueryBuilder().append(cls=(StructureData, ParameterData), filters={'attributes.cat': 'miau'},
                                   subclassing=False)
        self.assertEqual(qb.count(), 2)
        qb = QueryBuilder().append(cls=(StructureData, Data), filters={'attributes.cat': 'miau'}, )
        self.assertEqual(qb.count(), 3)
        qb = QueryBuilder().append(type=('data.structure.StructureData.', 'data.parameter.ParameterData.'),
                                   filters={'attributes.cat': 'miau'}, subclassing=False)
        self.assertEqual(qb.count(), 2)
        qb = QueryBuilder().append(type=('data.structure.StructureData.', 'data.Data.'),
                                   filters={'attributes.cat': 'miau'}, subclassing=False)
        self.assertEqual(qb.count(), 2)

    def test_list_behavior(self):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder

        for i in range(4):
            Data().store()

        self.assertEqual(len(QueryBuilder().append(Node).all()), 4)
        self.assertEqual(len(QueryBuilder().append(Node, project='*').all()), 4)
        self.assertEqual(len(QueryBuilder().append(Node, project=['*', 'id']).all()), 4)
        self.assertEqual(len(QueryBuilder().append(Node, project=['id']).all()), 4)
        self.assertEqual(len(QueryBuilder().append(Node).dict()), 4)
        self.assertEqual(len(QueryBuilder().append(Node, project='*').dict()), 4)
        self.assertEqual(len(QueryBuilder().append(Node, project=['*', 'id']).dict()), 4)
        self.assertEqual(len(QueryBuilder().append(Node, project=['id']).dict()), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node).iterall())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node, project='*').iterall())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node, project=['*', 'id']).iterall())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node, project=['id']).iterall())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node).iterdict())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node, project='*').iterdict())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node, project=['*', 'id']).iterdict())), 4)
        self.assertEqual(len(list(QueryBuilder().append(Node, project=['id']).iterdict())), 4)

    def test_append_validation(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.data.structure import StructureData
        from aiida.common.exceptions import InputValidationError
        from aiida.orm.node.process import ProcessNode

        # So here I am giving two times the same tag
        with self.assertRaises(InputValidationError):
            QueryBuilder().append(StructureData, tag='n').append(StructureData, tag='n')
        # here I am giving a wrong filter specifications
        with self.assertRaises(InputValidationError):
            QueryBuilder().append(StructureData, filters=['jajjsd'])
        # here I am giving a nonsensical projection:
        with self.assertRaises(InputValidationError):
            QueryBuilder().append(StructureData, project=True)

        # here I am giving a nonsensical projection for the edge:
        with self.assertRaises(InputValidationError):
            QueryBuilder().append(ProcessNode).append(StructureData, edge_tag='t').add_projection('t', True)
        # Giving a nonsensical limit
        with self.assertRaises(InputValidationError):
            QueryBuilder().append(ProcessNode).limit(2.3)
        # Giving a nonsensical offset
        with self.assertRaises(InputValidationError):
            QueryBuilder(offset=2.3)

        # So, I mess up one append, I want the QueryBuilder to clean it!
        with self.assertRaises(InputValidationError):
            qb = QueryBuilder()
            # This also checks if we correctly raise for wrong keywords
            qb.append(StructureData, tag='s', randomkeyword={})

        # Now I'm checking whether this keyword appears anywhere in the internal dictionaries:
        self.assertTrue('s' not in qb._projections)
        self.assertTrue('s' not in qb._filters)
        self.assertTrue('s' not in qb._tag_to_alias_map)
        self.assertTrue(len(qb._path) == 0)
        self.assertTrue(StructureData not in qb._cls_to_tag_map)
        # So this should work now:
        qb.append(StructureData, tag='s').limit(2).dict()

    def test_tags(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.node import Node
        from aiida.orm.node.process import ProcessNode
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.computers import Computer
        qb = QueryBuilder()
        qb.append(Node, tag='n1')
        qb.append(Node, tag='n2', edge_tag='e1', with_incoming='n1')
        qb.append(Node, tag='n3', edge_tag='e2', with_incoming='n2')
        qb.append(Computer, with_node='n3', tag='c1', edge_tag='nonsense')
        self.assertEqual(qb.get_used_tags(), ['n1', 'n2', 'e1', 'n3', 'e2', 'c1', 'nonsense'])

        # Now I am testing the default tags,
        qb = QueryBuilder().append(StructureData).append(ProcessNode).append(
            StructureData).append(
            ParameterData, with_outgoing=ProcessNode)
        self.assertEqual(qb.get_used_tags(), [
            'StructureData_1', 'ProcessNode_1',
            'StructureData_1--ProcessNode_1', 'StructureData_2',
            'ProcessNode_1--StructureData_2', 'ParameterData_1',
            'ProcessNode_1--ParameterData_1'
        ])
        self.assertEqual(qb.get_used_tags(edges=False), [
            'StructureData_1', 'ProcessNode_1',
            'StructureData_2', 'ParameterData_1',
        ])
        self.assertEqual(qb.get_used_tags(vertices=False), [
            'StructureData_1--ProcessNode_1',
            'ProcessNode_1--StructureData_2',
            'ProcessNode_1--ParameterData_1'
        ])


class TestQueryHelp(AiidaTestCase):
    def test_queryhelp(self):
        """
        Here I test the queryhelp by seeing whether results are the same as using the append method.
        I also check passing of tuples.
        """

        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.data import Data
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.groups import Group
        from aiida.orm.computers import Computer
        g = Group(label='helloworld').store()
        for cls in (StructureData, ParameterData, Data):
            obj = cls()
            obj._set_attr('foo-qh2', 'bar')
            obj.store()
            g.add_nodes(obj)

        for cls, expected_count, subclassing in (
                (StructureData, 1, True),
                (ParameterData, 1, True),
                (Data, 3, True),
                (Data, 1, False),
                ((ParameterData, StructureData), 2, True),
                ((ParameterData, StructureData), 2, False),
                ((ParameterData, Data), 2, False),
                ((ParameterData, Data), 3, True),
                ((ParameterData, Data, StructureData), 3, False),
        ):
            qb = QueryBuilder()
            qb.append(cls, filters={'attributes.foo-qh2': 'bar'}, subclassing=subclassing, project='uuid')
            self.assertEqual(qb.count(), expected_count)

            qh = qb.get_json_compatible_queryhelp()
            qb_new = QueryBuilder(**qh)
            self.assertEqual(qb_new.count(), expected_count)
            self.assertEqual(
                sorted([uuid for uuid, in qb.all()]),
                sorted([uuid for uuid, in qb_new.all()]))

        qb = QueryBuilder().append(Group, filters={'label': 'helloworld'})
        self.assertEqual(qb.count(), 1)

        qb = QueryBuilder().append((Group,), filters={'label': 'helloworld'})
        self.assertEqual(qb.count(), 1)

        qb = QueryBuilder().append(Computer, )
        self.assertEqual(qb.count(), 1)

        qb = QueryBuilder().append(cls=(Computer,))
        self.assertEqual(qb.count(), 1)


class TestQueryBuilderCornerCases(AiidaTestCase):
    """
    In this class corner cases of QueryBuilder are added.
    """

    def test_computer_json(self):
        """
        In this test we check the correct behavior of QueryBuilder when
        retrieving the _metadata and the transport_params with no content.
        Note that they are in JSON format in both backends. Forcing the
        decoding of a None value leads to an exception (this was the case
        under Django).
        """
        from aiida.orm import Node, Data, Computer
        from aiida.orm.node.process import ProcessNode
        from aiida.orm.querybuilder import QueryBuilder

        n1 = CalculationNode()
        n1.label = 'node2'
        n1._set_attr('foo', 1)
        n1.store()

        # Checking the correct retrieval of transport_params which is
        # a JSON field (in both backends).
        qb = QueryBuilder()
        qb.append(CalculationNode, project=['id'], tag='calc')
        qb.append(Computer, project=['id', 'transport_params'],
                  outerjoin=True, with_node='calc')
        qb.all()

        # Checking the correct retrieval of _metadata which is
        # a JSON field (in both backends).
        qb = QueryBuilder()
        qb.append(CalculationNode, project=['id'], tag='calc')
        qb.append(Computer, project=['id', '_metadata'],
                  outerjoin=True, with_node='calc')
        qb.all()


class TestAttributes(AiidaTestCase):
    def test_attribute_existence(self):
        # I'm storing a value under key whatever:
        from aiida.orm.node import Node
        from aiida.orm.querybuilder import QueryBuilder
        val = 1.
        res_uuids = set()
        n1 = Data()
        n1._set_attr("whatever", 3.)
        n1._set_attr("test_case", "test_attribute_existence")
        n1.store()

        # I want all the nodes where whatever is smaller than 1. or there is no such value:

        qb = QueryBuilder()
        qb.append(Data, filters={
            'or': [
                {'attributes': {'!has_key': 'whatever'}},
                {'attributes.whatever': {'<': val}}
            ],
        }, project='uuid')
        res_query = set([str(_[0]) for _ in qb.all()])
        self.assertEqual(res_query, res_uuids)

    def test_attribute_type(self):
        from aiida.orm.node import Node
        from aiida.orm.querybuilder import QueryBuilder
        key = 'value_test_attr_type'
        n_int, n_float, n_str, n_str2, n_bool, n_arr = [Data() for _ in range(6)]
        n_int._set_attr(key, 1)
        n_float._set_attr(key, 1.0)
        n_bool._set_attr(key, True)
        n_str._set_attr(key, '1')
        n_str2._set_attr(key, 'one')
        n_arr._set_attr(key, [4, 3, 5])
        [n.store() for n in (n_str2, n_str, n_int, n_float, n_bool, n_arr)]
        # Here I am testing which values contain a number 1.
        # Both 1 and 1.0 are legitimate values if ask for either 1 or 1.0
        for val in (1.0, 1):
            qb = QueryBuilder().append(Node,
                    filters={'attributes.{}'.format(key): val}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_float.uuid, n_int.uuid)))
            qb = QueryBuilder().append(Node,
                    filters={'attributes.{}'.format(key): {'>': 0.5}}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_float.uuid, n_int.uuid)))
            qb = QueryBuilder().append(Node,
                    filters={'attributes.{}'.format(key): {'<': 1.5}}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_float.uuid, n_int.uuid)))
        # Now I am testing the boolean value:
        qb = QueryBuilder().append(Node,
                filters={'attributes.{}'.format(key): True}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_bool.uuid,)))

        qb = QueryBuilder().append(Node,
                filters={'attributes.{}'.format(key): {'like': '%n%'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str2.uuid,)))
        qb = QueryBuilder().append(Node,
                filters={'attributes.{}'.format(key): {'ilike': 'On%'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str2.uuid,)))
        qb = QueryBuilder().append(Node,
                filters={'attributes.{}'.format(key): {'like': '1'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str.uuid,)))
        qb = QueryBuilder().append(Node,
                filters={'attributes.{}'.format(key): {'==': '1'}}, project='uuid')
        res = [str(_) for _, in qb.all()]
        self.assertEqual(set(res), set((n_str.uuid,)))
        if settings.BACKEND == u'sqlalchemy':
            # I can't query the length of an array with Django,
            # so I exclude. Not the nicest way, But I would like to keep this piece
            # of code because of the initialization part, that would need to be
            # duplicated or wrapped otherwise.
            qb = QueryBuilder().append(Node,
                    filters={'attributes.{}'.format(key): {'of_length': 3}}, project='uuid')
            res = [str(_) for _, in qb.all()]
            self.assertEqual(set(res), set((n_arr.uuid,)))


class QueryBuilderDateTimeAttribute(AiidaTestCase):
    @unittest.skipIf(settings.BACKEND == u'sqlalchemy',
                     "SQLA doesn't have full datetime support in attributes")
    def test_date(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.common import timezone
        from datetime import timedelta
        from aiida.orm.node import Node
        n = Data()
        now = timezone.now()
        n._set_attr('now', now)
        n.store()

        qb = QueryBuilder().append(Node,
                                   filters={'attributes.now': {"and": [
                                       {">": now - timedelta(seconds=1)},
                                       {"<": now + timedelta(seconds=1)},
                                   ]}})
        self.assertEqual(qb.count(), 1)


class QueryBuilderLimitOffsetsTest(AiidaTestCase):

    def test_ordering_limits_offsets_of_results_general(self):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder
        # Creating 10 nodes with an attribute that can be ordered
        for i in range(10):
            n = Data()
            n._set_attr('foo', i)
            n.store()

        qb = QueryBuilder().append(
            Node, project='attributes.foo'
        ).order_by({Node: 'ctime'})

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
        qb = QueryBuilder().append(
            Node, project='attributes.foo'
        ).order_by({Node: {'ctime': {'order': 'asc'}}})

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
        qb = QueryBuilder().append(
            Node, project='attributes.foo'
        ).order_by({Node: {'ctime': {'order': 'desc'}}})

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
        from aiida.orm import Node, Data
        from aiida.orm.querybuilder import QueryBuilder
        # Creating n1, who will be a parent:
        parent = Data()
        parent.label = 'mother'

        good_child = CalculationNode()
        good_child.label = 'good_child'
        good_child._set_attr('is_good', True)

        bad_child = CalculationNode()
        bad_child.label = 'bad_child'
        bad_child._set_attr('is_good', False)

        unrelated = CalculationNode()
        unrelated.label = 'unrelated'

        for n in (good_child, bad_child, parent, unrelated):
            n.store()

        good_child.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='parent')
        bad_child.add_incoming(parent, link_type=LinkType.INPUT_CALC, link_label='parent')

        # Using a standard inner join
        qb = QueryBuilder()
        qb.append(Node, tag='parent')
        qb.append(Node, tag='children', project='label', filters={'attributes.is_good': True})
        self.assertEqual(qb.count(), 1)

        qb = QueryBuilder()
        qb.append(Node, tag='parent')
        qb.append(Node, tag='children', outerjoin=True, project='label', filters={'attributes.is_good': True})
        self.assertEqual(qb.count(), 1)

    def test_joins2(self):
        from aiida.orm import Node, Data
        from aiida.orm.querybuilder import QueryBuilder
        # Creating n1, who will be a parent:

        students = [Data() for i in range(10)]
        advisors = [CalculationNode() for i in range(3)]
        for i, a in enumerate(advisors):
            a.label = 'advisor {}'.format(i)
            a._set_attr('advisor_id', i)

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
            QueryBuilder().append(
                Node
            ).append(
                Node, edge_filters={'label': {'like': 'is\\_advisor\\_%'}}, tag='student'
            ).count(), 7)

        for adv_id, number_students in zip(list(range(3)), (2, 2, 3)):
            self.assertEqual(QueryBuilder().append(
                Node, filters={'attributes.advisor_id': adv_id}
            ).append(
                Node, edge_filters={'label': {'like': 'is\\_advisor\\_%'}}, tag='student'
            ).count(), number_students)

    def test_joins3_user_group(self):
        from aiida import orm

        # Create another user
        new_email = "newuser@new.n"
        user = orm.User(email=new_email).store()

        # Create a group that belongs to that user
        from aiida.orm.groups import Group
        group = orm.Group(label="node_group")
        group.user = user
        group.store()

        # Search for the group of the user
        qb = orm.QueryBuilder()
        qb.append(orm.User, tag='user', filters={'id': {'==': user.id}})
        qb.append(orm.Group, with_user='user',
                  filters={'id': {'==': group.id}})
        self.assertEquals(qb.count(), 1, "The expected group that belongs to "
                                         "the selected user was not found.")

        # Search for the user that owns a group
        qb = orm.QueryBuilder()
        qb.append(orm.Group, tag='group', filters={'id': {'==': group.id}})
        qb.append(orm.User, with_group='group', filters={'id': {'==': user.id}})

        self.assertEquals(qb.count(), 1, "The expected user that owns the "
                                         "selected group was not found.")


class QueryBuilderPath(AiidaTestCase):
    def test_query_path(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node
        from aiida.common.links import LinkType

        q = self.backend.query_manager
        n1 = Data()
        n1.label = 'n1'
        n1.store()
        n2 = CalculationNode()
        n2.label = 'n2'
        n2.store()
        n3 = Data()
        n3.label = 'n3'
        n3.store()
        n4 = Data()
        n4.label = 'n4'
        n4.store()
        n5 = CalculationNode()
        n5.label = 'n5'
        n5.store()
        n6 = Data()
        n6.label = 'n6'
        n6.store()
        n7 = CalculationNode()
        n7.label = 'n7'
        n7.store()
        n8 = Data()
        n8.label = 'n8'
        n8.store()
        n9 = Data()
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
        self.assertEqual(set([(_,) for _ in (n6.pk,)]), set([tuple(_) for _ in q.get_all_parents([n7.pk])]))
        # There are several parents to n4
        self.assertEqual(set([(_.pk,) for _ in (n1, n2)]), set([tuple(_) for _ in q.get_all_parents([n4.pk])]))
        # There are several parents to n5
        self.assertEqual(set([(_.pk,) for _ in (n1, n2, n3, n4)]), set([tuple(_) for _ in q.get_all_parents([n5.pk])]))

        # Yet, no links from 1 to 8
        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n1.pk}, tag='anc'
            ).append(Node, with_ancestors='anc', filters={'id': n8.pk}
                     ).count(), 0)

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}
                     ).count(), 0)

        n6.add_incoming(n5, link_type=LinkType.CREATE, link_label='link1')
        # Yet, now 2 links from 1 to 8
        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n1.pk}, tag='anc'
            ).append(Node, with_ancestors='anc', filters={'id': n8.pk}
                     ).count(), 2
        )

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}
                     ).count(), 2)

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}, edge_filters={'depth': {'<': 6}},
                     ).count(), 2)
        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}, edge_filters={'depth': 5},
                     ).count(), 2)
        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}, edge_filters={'depth': {'<': 5}},
                     ).count(), 0)

        # TODO write a query that can filter certain paths by traversed ID
        qb = QueryBuilder().append(
            Node, filters={'id': n8.pk}, tag='desc',
        ).append(Node, with_descendants='desc', edge_project='path', filters={'id': n1.pk})
        queried_path_set = set([frozenset(p) for p, in qb.all()])

        paths_there_should_be = set([
            frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
            frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk])
        ])

        self.assertTrue(queried_path_set == paths_there_should_be)

        qb = QueryBuilder().append(
            Node, filters={'id': n1.pk}, tag='anc'
        ).append(
            Node, with_ancestors='anc', filters={'id': n8.pk}, edge_project='path'
        )

        self.assertTrue(set(
            [frozenset(p) for p, in qb.all()]
        ) == set(
            [frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
             frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk])]
        ))

        n7.add_incoming(n9, link_type=LinkType.INPUT_CALC, link_label='link0')
        # Still two links...

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n1.pk}, tag='anc'
            ).append(Node, with_ancestors='anc', filters={'id': n8.pk}
                     ).count(), 2
        )

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}
                     ).count(), 2)
        n9.add_incoming(n5, link_type=LinkType.CREATE, link_label='link6')
        # And now there should be 4 nodes

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n1.pk}, tag='anc'
            ).append(Node, with_ancestors='anc', filters={'id': n8.pk}
                     ).count(), 4)

        self.assertEquals(
            QueryBuilder().append(
                Node, filters={'id': n8.pk}, tag='desc'
            ).append(Node, with_descendants='desc', filters={'id': n1.pk}
                     ).count(), 4)

        qb = QueryBuilder().append(
            Node, filters={'id': n1.pk}, tag='anc'
        ).append(
            Node, with_ancestors='anc', filters={'id': n8.pk}, edge_tag='edge'
        )
        qb.add_projection('edge', 'depth')
        self.assertTrue(set(next(zip(*qb.all()))), set([5, 6]))
        qb.add_filter('edge', {'depth': 5})
        self.assertTrue(set(next(zip(*qb.all()))), set([5]))


class TestConsistency(AiidaTestCase):
    def test_create_node_and_query(self):
        """
        Testing whether creating nodes within a iterall iteration changes the results.
        """
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder
        import random

        for i in range(100):
            n = Data()
            n.store()

        for idx, item in enumerate(QueryBuilder().append(Node, project=['id', 'label']).iterall(batch_size=10)):
            if idx % 10 == 10:
                n = Data()
                n.store()
        self.assertEqual(idx, 99)
        self.assertTrue(len(QueryBuilder().append(Node, project=['id', 'label']).all(batch_size=10)) > 99)

    def test_len_results(self):
        """
        Test whether the len of results matches the count returned.
        See also https://github.com/aiidateam/aiida_core/issues/1600
        SQLAlchemy has a deduplication strategy that leads to strange behavior, tested against here
        """
        from aiida.orm import Data
        from aiida.orm.node.process import CalculationNode
        from aiida.orm.querybuilder import QueryBuilder

        parent = CalculationNode().store()
        # adding 5 links going out:
        for inode in range(5):
            output_node = Data().store()
            output_node.add_incoming(parent, link_type=LinkType.CREATE, link_label='link-{}'.format(inode))
        for projection in ('id', '*'):
            qb = QueryBuilder()
            qb.append(CalculationNode, filters={'id':parent.id}, tag='parent', project=projection)
            qb.append(Data, with_incoming='parent')
            self.assertEqual(len(qb.all()), qb.count())

class TestManager(AiidaTestCase):
    def test_statistics(self):
        """
        Test if the statistics query works properly.

        I try to implement it in a way that does not depend on the past state.
        """
        from aiida.orm import Node, DataFactory
        from aiida.orm.node.process import ProcessNode
        from collections import defaultdict

        def store_and_add(n, statistics):
            n.store()
            statistics['total'] += 1
            statistics['types'][n._plugin_type_string] += 1
            statistics['ctime_by_day'][n.ctime.strftime('%Y-%m-%d')] += 1

        qmanager = self.backend.query_manager
        current_db_statistics = qmanager.get_creation_statistics()
        types = defaultdict(int)
        types.update(current_db_statistics['types'])
        ctime_by_day = defaultdict(int)
        ctime_by_day.update(current_db_statistics['ctime_by_day'])

        expected_db_statistics = {
            'total': current_db_statistics['total'],
            'types': types,
            'ctime_by_day': ctime_by_day
        }

        ParameterData = DataFactory('parameter')

        store_and_add(Data(), expected_db_statistics)
        store_and_add(ParameterData(), expected_db_statistics)
        store_and_add(ParameterData(), expected_db_statistics)
        store_and_add(CalculationNode(), expected_db_statistics)

        new_db_statistics = qmanager.get_creation_statistics()
        # I only check a few fields
        new_db_statistics = {k: v for k, v in new_db_statistics.items() if k in expected_db_statistics}

        expected_db_statistics = {k: dict(v) if isinstance(v, defaultdict) else v
                                  for k, v in expected_db_statistics.items()}

        self.assertEquals(new_db_statistics, expected_db_statistics)

    def test_statistics_default_class(self):
        """
        Test if the statistics query works properly.

        I try to implement it in a way that does not depend on the past state.
        """
        from aiida.orm import Node, DataFactory
        from aiida.orm.node.process import ProcessNode
        from collections import defaultdict

        def store_and_add(n, statistics):
            n.store()
            statistics['total'] += 1
            statistics['types'][n._plugin_type_string] += 1
            statistics['ctime_by_day'][n.ctime.strftime('%Y-%m-%d')] += 1

        current_db_statistics = self.backend.query_manager.get_creation_statistics()
        types = defaultdict(int)
        types.update(current_db_statistics['types'])
        ctime_by_day = defaultdict(int)
        ctime_by_day.update(current_db_statistics['ctime_by_day'])

        expected_db_statistics = {
            'total': current_db_statistics['total'],
            'types': types,
            'ctime_by_day': ctime_by_day
        }

        ParameterData = DataFactory('parameter')

        store_and_add(Data(), expected_db_statistics)
        store_and_add(ParameterData(), expected_db_statistics)
        store_and_add(ParameterData(), expected_db_statistics)
        store_and_add(CalculationNode(), expected_db_statistics)

        new_db_statistics = self.backend.query_manager.get_creation_statistics()
        # I only check a few fields
        new_db_statistics = {k: v for k, v in new_db_statistics.items() if k in expected_db_statistics}

        expected_db_statistics = {k: dict(v) if isinstance(v, defaultdict) else v
                                  for k, v in expected_db_statistics.items()}

        self.assertEquals(new_db_statistics, expected_db_statistics)
