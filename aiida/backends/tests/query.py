# -*- coding: utf-8 -*-

import unittest
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.querybuilder import QueryBuilder
from aiida.utils import timezone
from aiida.settings import BACKEND

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


class TestQueryBuilder(AiidaTestCase):
    def test_classification(self):
        """
        This tests the classifications of the QueryBuilder
        """
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
        from aiida.orm import Node, Data, Calculation
        from aiida.common.links import LinkType

        n1 = Data()
        n1.label = 'node1'
        n1._set_attr('foo', ['hello', 'goodbye'])
        n1.store()

        n2 = Calculation()
        n2.label = 'node2'
        n2._set_attr('foo', 1)
        n2.store()

        n3 = Data()
        n3.label = 'node3'
        n3._set_attr('foo', 1.0000)  # Stored as fval
        n3.store()

        n4 = Calculation()
        n4.label = 'node4'
        n4._set_attr('foo', 'bar')
        n4.store()

        n5 = Data()
        n5.label = 'node5'
        n5._set_attr('foo', None)
        n5.store()

        n2.add_link_from(n1, link_type=LinkType.INPUT)
        n3.add_link_from(n2, link_type=LinkType.CREATE)

        n4.add_link_from(n3, link_type=LinkType.INPUT)
        n5.add_link_from(n4, link_type=LinkType.CREATE)

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
        qb4.append(Calculation, tag='node1')
        qb4.append(Data, tag='node2')
        self.assertEqual(qb4.count(), 2)

        qb5 = QueryBuilder()
        qb5.append(Data, tag='node1')
        qb5.append(Calculation, tag='node2')
        self.assertEqual(qb5.count(), 2)

        qb6 = QueryBuilder()
        qb6.append(Data, tag='node1')
        qb6.append(Data, tag='node2')
        self.assertEqual(qb6.count(), 0)

    def test_simple_query_2(self):
        from aiida.orm import Node
        from datetime import datetime

        n0 = Node()
        n0.label = 'hello'
        n0.description = ''
        n0._set_attr('foo', 'bar')

        n1 = Node()
        n1.label = 'foo'
        n1.description = 'I am FoO'

        n2 = Node()
        n2.label = 'bar'
        n2.description = 'I am BaR'

        n2.add_link_from(n1, label='random_2')
        n1.add_link_from(n0, label='random_1')

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
                    'output_of': 'n1'
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

        resdict = resdict[0]
        self.assertTrue(isinstance(resdict['n1']['ctime'], datetime))
        self.assertEqual(resdict['n2']['label'], 'bar')

        qh = {
            'path': [
                {
                    'cls': Node,
                    'tag': 'n1'
                },
                {
                    'cls': Node,
                    'tag': 'n2',
                    'output_of': 'n1'
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

        query2 = qb.get_query()
        query3 = qb.get_query()

        self.assertTrue(id(query1) != id(query2))
        self.assertTrue(id(query2) == id(query3))

    def test_operators_eq_lt_gt(self):
        from aiida.orm import Node

        nodes = [Node() for _ in range(8)]

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
        s = StructureData()
        s._set_attr('cat', 'miau')
        s.store()

        d = Data()
        d._set_attr('cat', 'miau')
        d.store()

        p = ParameterData(dict=dict(cat='miau'))
        p.store()

        n = Node()
        n._set_attr('cat', 'miau')
        n.store()

        # Now when asking for a node with attr.cat==miau, I want 4 esults:
        qb = QueryBuilder().append(Node, filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 4)

        qb = QueryBuilder().append(Data, filters={'attributes.cat': 'miau'})
        self.assertEqual(qb.count(), 3)

        # If I'm asking for the specific lowest subclass, I want one result
        for cls in (StructureData, ParameterData):
            qb = QueryBuilder().append(cls, filters={'attributes.cat': 'miau'})
            self.assertEqual(qb.count(), 1)

        # Now I am not allow the subclassing, which should give 1 result for each
        for cls in (StructureData, ParameterData, Node, Data):
            qb = QueryBuilder().append(cls, filters={'attributes.cat': 'miau'}, subclassing=False)
            self.assertEqual(qb.count(), 1)

    @unittest.skipIf(BACKEND == u'sqlalchemy',
                     "SQLA doesn't have full datetime support in attributes")
    def test_datetime_attribute(self):
        from aiida.orm import Calculation
        c = Calculation()
        now = timezone.now()
        c._set_attr('now', now)
        c.store()

        q = QueryBuilder()
        q.append(Calculation, filters={'attributes.now': now})

        self.assertEqual(len(q.all()), 1)


class QueryBuilderJoinsTests(AiidaTestCase):
    def test_joins1(self):
        from aiida.orm import Node, Data, Calculation
        # Creating n1, who will be a parent:
        parent = Node()
        parent.label = 'mother'

        good_child = Node()
        good_child.label = 'good_child'
        good_child._set_attr('is_good', True)

        bad_child = Node()
        bad_child.label = 'bad_child'
        bad_child._set_attr('is_good', False)

        unrelated = Node()
        unrelated.label = 'unrelated'

        for n in (good_child, bad_child, parent, unrelated):
            n.store()

        good_child.add_link_from(parent, label='parent')
        bad_child.add_link_from(parent, label='parent')

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
        from aiida.orm import Node, Data, Calculation
        # Creating n1, who will be a parent:

        students = [Node() for i in range(10)]
        advisors = [Node() for i in range(3)]
        for i, a in enumerate(advisors):
            a.label = 'advisor {}'.format(i)
            a._set_attr('advisor_id', i)

        for n in advisors + students:
            n.store()

        # advisor 0 get student 0, 1
        for i in (0, 1):
            students[i].add_link_from(advisors[0], label='is_advisor')

        # advisor 1 get student 3, 4
        for i in (3, 4):
            students[i].add_link_from(advisors[1], label='is_advisor')

        # advisor 2 get student 5, 6, 7
        for i in (5, 6, 7):
            students[i].add_link_from(advisors[2], label='is_advisor')

        # let's add a differnt relationship than advisor:
        students[9].add_link_from(advisors[2], label='lover')

        self.assertEqual(
            QueryBuilder().append(
                Node
            ).append(
                Node, edge_filters={'label': 'is_advisor'}, tag='student'
            ).count(), 7)

        for adv_id, number_students in zip(range(3), (2, 2, 3)):
            self.assertEqual(QueryBuilder().append(
                Node, filters={'attributes.advisor_id': adv_id}
            ).append(
                Node, edge_filters={'label': 'is_advisor'}, tag='student'
            ).count(), number_students)


class QueryBuilderPath(AiidaTestCase):
    def test_query_path(self):

        from aiida.orm import Node

        n1 = Node()
        n1.label = 'n1'
        n1.store()
        n2 = Node()
        n2.label = 'n2'
        n2.store()
        n3 = Node()
        n3.label = 'n3'
        n3.store()
        n4 = Node()
        n4.label = 'n4'
        n4.store()
        n5 = Node()
        n5.label = 'n5'
        n5.store()
        n6 = Node()
        n6.label = 'n6'
        n6.store()
        n7 = Node()
        n7.label = 'n7'
        n7.store()
        n8 = Node()
        n8.label = 'n8'
        n8.store()
        n9 = Node()
        n9.label = 'n9'
        n9.store()

        # I create a strange graph, inserting links in a order
        # such that I often have to create the transitive closure
        # between two graphs
        n3.add_link_from(n2)
        n2.add_link_from(n1)
        n5.add_link_from(n3)
        n5.add_link_from(n4)
        n4.add_link_from(n2)

        n7.add_link_from(n6)
        n8.add_link_from(n7)

        for with_dbpath in (True, False):
            # Yet, no links from 1 to 8
            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc', filters={'id': n8.pk}
                         ).count(), 0)

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc', filters={'id': n1.pk}
                         ).count(), 0)

        n6.add_link_from(n5)
        # Yet, now 2 links from 1 to 8


        for with_dbpath in (True, False):
            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc', filters={'id': n8.pk}
                         ).count(), 2
            )

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc', filters={'id': n1.pk}
                         ).count(), 2)

        n7.add_link_from(n9)
        # Still two links...

        for with_dbpath in (True, False):
            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc', filters={'id': n8.pk}
                         ).count(), 2
            )

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc', filters={'id': n1.pk}
                         ).count(), 2)
        n9.add_link_from(n6)
        # And now there should be 4 nodes
        for with_dbpath in (True, False):
            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc', filters={'id': n8.pk}
                         ).count(), 4)

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                    Node, filters={'id': n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc', filters={'id': n1.pk}
                         ).count(), 4)

        for with_dbpath in (True, False):
            qb = QueryBuilder(with_dbpath=True).append(
                Node, filters={'id': n1.pk}, tag='anc'
            ).append(
                Node, descendant_of='anc', filters={'id': n8.pk}, edge_tag='edge'
            )
            qb.add_projection('edge', 'depth')
            self.assertTrue(set(zip(*qb.all())[0]), set([5, 6]))
            qb.add_filter('edge', {'depth': 6})
            self.assertTrue(set(zip(*qb.all())[0]), set([6]))
