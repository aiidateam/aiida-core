# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase
import unittest
import aiida.backends.settings as settings




class TestQueryBuilder(AiidaTestCase):

    def test_classification(self):
        """
        This tests the classifications of the QueryBuilder
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.utils import (DataFactory, CalculationFactory)
        from aiida.orm.data.structure import StructureData
        from aiida.orm import Group, User, Node, Computer, Data, Calculation
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
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm import Node, Data, Calculation
        from datetime import datetime
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
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node
        from datetime import datetime
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        n0 = Node()
        n0.label = 'hello'
        n0.description=''
        n0._set_attr('foo', 'bar')

        n1 = Node()
        n1.label='foo'
        n1.description='I am FoO'

        n2 = Node()
        n2.label='bar'
        n2.description='I am BaR'

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

        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa':{'<':1}}).count(), 0)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa':{'==':1}}).count(), 2)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa':{'<':1.02}}).count(), 3)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa':{'<=':1.02}}).count(), 4)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa':{'>':1.02}}).count(), 4)
        self.assertEqual(QueryBuilder().append(Node, filters={'attributes.fa':{'>=':1.02}}).count(), 5)




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

        n = Node()
        n._set_attr('cat', 'miau')
        n.store()

        # Now when asking for a node with attr.cat==miau, I want 4 esults:
        qb = QueryBuilder().append(Node, filters={'attributes.cat':'miau'})
        self.assertEqual(qb.count(), 4)

        qb = QueryBuilder().append(Data, filters={'attributes.cat':'miau'})
        self.assertEqual(qb.count(), 3)

        # If I'm asking for the specific lowest subclass, I want one result
        for cls in (StructureData, ParameterData):
            qb = QueryBuilder().append(cls, filters={'attributes.cat':'miau'})
            self.assertEqual(qb.count(), 1)

        # Now I am not allow the subclassing, which should give 1 result for each
        for cls in (StructureData, ParameterData, Node, Data):
            qb = QueryBuilder().append(cls, filters={'attributes.cat':'miau'}, subclassing=False)
            self.assertEqual(qb.count(), 1)


    def test_list_behavior(self):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder

        for i in range(4):
            Node().store()
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
        from aiida.orm import Calculation


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
            QueryBuilder().append(Calculation).append(StructureData, edge_tag='t').add_projection('t', True)
        # Giving a nonsensical limit
        with self.assertRaises(InputValidationError):
            QueryBuilder().append(Calculation).limit(2.3)
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
        self.assertTrue(len(qb._path)==0)
        self.assertTrue(StructureData not in qb._cls_to_tag_map)
        # So this should work now:
        qb.append(StructureData, tag='s').limit(2).dict()

    def test_tags(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.node import Node
        from aiida.orm.calculation import Calculation
        from aiida.orm.data.structure import StructureData
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.computer import Computer
        qb = QueryBuilder()
        qb.append(Node, tag='n1')
        qb.append(Node, tag='n2', edge_tag='e1', output_of='n1')
        qb.append(Node, tag='n3', edge_tag='e2', output_of='n2')
        qb.append(Computer, computer_of='n3', tag='c1')
        self.assertEqual(qb.get_used_tags(), ['n1', 'n2','e1', 'n3', 'e2', 'c1'])


        # Now I am testing the default tags,
        qb = QueryBuilder().append(StructureData).append(Calculation).append(
            StructureData).append(
            ParameterData, input_of=Calculation)
        self.assertEqual(qb.get_used_tags(), [
                'StructureData_1', 'Calculation_1',
                'StructureData_1--Calculation_1', 'StructureData_2',
                'Calculation_1--StructureData_2', 'ParameterData_1',
                'Calculation_1--ParameterData_1'
            ])
        self.assertEqual(qb.get_used_tags(edges=False), [
                'StructureData_1', 'Calculation_1',
                'StructureData_2', 'ParameterData_1',
            ])
        self.assertEqual(qb.get_used_tags(vertices=False), [
                'StructureData_1--Calculation_1',
                'Calculation_1--StructureData_2',
                'Calculation_1--ParameterData_1'
            ])


class TestAttributes(AiidaTestCase):
    def test_attribute_existence(self):
        # I'm storing a value under key whatever:
        from aiida.orm.node import Node
        from aiida.orm.querybuilder import QueryBuilder
        val = 1.
        res_uuids = set()
        n1 = Node()
        n1._set_attr("whatever", 3.)
        n1._set_attr("test_case", "test_attribute_existence")
        n1.store()

        n1 = Node()
        n1._set_attr("whatever", 0.)
        n1._set_attr("test_case", "test_attribute_existence")
        n1.store()
        res_uuids.add(n1.uuid)

        n1 = Node()
        n1._set_attr("whatever", None)
        n1._set_attr("test_case", "test_attribute_existence")
        n1.store()

        n1 = Node()
        n1._set_attr("test_case", "test_attribute_existence")
        n1.store()
        res_uuids.add(n1.uuid)

        # I want all the nodes where whatever is smaller than 1. or there is no such value:

        qb = QueryBuilder()
        qb.append(Node, filters={
                    'or':[
                        {'attributes': {'!has_key': 'whatever'}},
                        {'attributes.whatever':{'<':val}}
                    ],
            }, project='uuid')
        res_query = set([str(_[0]) for _ in qb.all()])
        self.assertEqual(res_query, res_uuids)



class QueryBuilderDateTimeAttribute(AiidaTestCase):
    @unittest.skipIf(settings.BACKEND == u'sqlalchemy',
              "SQLA doesn't have full datetime support in attributes")
    def test_date(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.utils import timezone
        from datetime import timedelta
        from aiida.orm.node import Node
        n = Node()
        now = timezone.now()
        n._set_attr('now', now)
        n.store()

        qb = QueryBuilder().append(Node,
            filters={'attributes.now': {"and":[
                {">":now-timedelta(seconds=1)},
                {"<":now+timedelta(seconds=1)},
            ]}})
        self.assertEqual(qb.count(), 1)




class QueryBuilderLimitOffsetsTest(AiidaTestCase):

    def test_ordering_limits_offsets_of_results_general(self):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder
        # Creating 10 nodes with an attribute that can be ordered
        for i in range(10):
            n = Node()
            n._set_attr('foo', i)
            n.store()

        qb = QueryBuilder().append(
                Node, project='attributes.foo'
            ).order_by({Node:'ctime'})

        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(10))

        # Now applying an offset:
        qb.offset(5)
        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(5,10))

        # Now also applying a limit:
        qb.limit(3)
        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(5,8))

        # Specifying the order  explicitly the order:
        qb = QueryBuilder().append(
                Node, project='attributes.foo'
            ).order_by({Node:{'ctime':{'order':'asc'}}})

        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(10))

        # Now applying an offset:
        qb.offset(5)
        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(5,10))

        # Now also applying a limit:
        qb.limit(3)
        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(5,8))


        # Reversing the order:
        qb = QueryBuilder().append(
                Node, project='attributes.foo'
            ).order_by({Node:{'ctime':{'order':'desc'}}})

        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(9, -1, -1))


        # Now applying an offset:
        qb.offset(5)
        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(4,-1,-1))

        # Now also applying a limit:
        qb.limit(3)
        res = list(zip(*qb.all())[0])
        self.assertEqual(res, range(4,1, -1))


class QueryBuilderJoinsTests(AiidaTestCase):
    def test_joins1(self):
        from aiida.orm import Node, Data, Calculation
        from aiida.orm.querybuilder import QueryBuilder
        # Creating n1, who will be a parent:
        parent=Node()
        parent.label = 'mother'

        good_child=Node()
        good_child.label='good_child'
        good_child._set_attr('is_good', True)

        bad_child=Node()
        bad_child.label='bad_child'
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
        qb.append(Node, tag='children', project='label', filters={'attributes.is_good':True})
        self.assertEqual(qb.count(), 1)


        qb = QueryBuilder()
        qb.append(Node, tag='parent')
        qb.append(Node, tag='children', outerjoin=True, project='label', filters={'attributes.is_good':True})
        self.assertEqual(qb.count(), 1)

    def test_joins2(self):
        from aiida.orm import Node, Data, Calculation
        from aiida.orm.querybuilder import QueryBuilder
        # Creating n1, who will be a parent:

        students = [Node() for i in range(10)]
        advisors = [Node() for i in range(3)]
        for i, a in enumerate(advisors):
            a.label = 'advisor {}'.format(i)
            a._set_attr('advisor_id', i)

        for n in advisors+students:
            n.store()


        # advisor 0 get student 0, 1
        for i in (0,1):
            students[i].add_link_from(advisors[0], label='is_advisor')

        # advisor 1 get student 3, 4
        for i in (3,4):
            students[i].add_link_from(advisors[1], label='is_advisor')

        # advisor 2 get student 5, 6, 7
        for i in (5,6,7):
            students[i].add_link_from(advisors[2], label='is_advisor')

        # let's add a differnt relationship than advisor:
        students[9].add_link_from(advisors[2], label='lover')


        self.assertEqual(
            QueryBuilder().append(
                    Node
                ).append(
                    Node, edge_filters={'label':'is_advisor'}, tag='student'
                ).count(), 7)

        for adv_id, number_students in zip(range(3), (2,2,3)):
            self.assertEqual(QueryBuilder().append(
                    Node, filters={'attributes.advisor_id':adv_id}
                ).append(
                    Node, edge_filters={'label':'is_advisor'}, tag='student'
                ).count(), number_students)


class QueryBuilderPath(AiidaTestCase):
    def test_query_path(self):

        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node

        n1 = Node()
        n1.label='n1'
        n1.store()
        n2 = Node()
        n2.label='n2'
        n2.store()
        n3 = Node()
        n3.label='n3'
        n3.store()
        n4 = Node()
        n4.label='n4'
        n4.store()
        n5 = Node()
        n5.label='n5'
        n5.store()
        n6 = Node()
        n6.label='n6'
        n6.store()
        n7 = Node()
        n7.label='n7'
        n7.store()
        n8 = Node()
        n8.label='n8'
        n8.store()
        n9 = Node()
        n9.label='n9'
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
                        Node, filters={'id':n1.pk}, tag='anc'
                    ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                    ).count(), 0)


            self.assertEquals(
                    QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n8.pk}, tag='desc'
                    ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                    ).count(), 0)


        n6.add_link_from(n5)
        # Yet, now 2 links from 1 to 8


        for with_dbpath in (True, False):

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n1.pk}, tag='anc'
                    ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                    ).count(), 2
                )

            self.assertEquals(
                    QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n8.pk}, tag='desc'
                    ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                    ).count(), 2)

        qb = QueryBuilder(with_dbpath=False,expand_path=True).append(
                Node, filters={'id':n8.pk}, tag='desc',
            ).append(Node, ancestor_of='desc', edge_project='path', filters={'id':n1.pk})
        queried_path_set = set([frozenset(p) for p, in qb.all()])

        paths_there_should_be = set([
                frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
                frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk])
            ])

        self.assertTrue(queried_path_set == paths_there_should_be)

        qb = QueryBuilder(with_dbpath=False, expand_path=True).append(
                Node, filters={'id':n1.pk}, tag='anc'
            ).append(
                Node, descendant_of='anc',  filters={'id':n8.pk}, edge_project='path'
            )

        self.assertTrue(set(
                [frozenset(p) for p, in qb.all()]
            ) == set(
                [frozenset([n1.pk, n2.pk, n3.pk, n5.pk, n6.pk, n7.pk, n8.pk]),
                frozenset([n1.pk, n2.pk, n4.pk, n5.pk, n6.pk, n7.pk, n8.pk])]
            ))

        n7.add_link_from(n9)
        # Still two links...

        for with_dbpath in (True, False):
            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n1.pk}, tag='anc'
                    ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                    ).count(), 2
                )

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n8.pk}, tag='desc'
                    ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                    ).count(), 2)
        n9.add_link_from(n6)
        # And now there should be 4 nodes
        for with_dbpath in (True, False):
            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n1.pk}, tag='anc'
                    ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                    ).count(), 4)

            self.assertEquals(
                QueryBuilder(with_dbpath=with_dbpath).append(
                        Node, filters={'id':n8.pk}, tag='desc'
                    ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                    ).count(), 4)


        for with_dbpath in (True, False):
            qb = QueryBuilder(with_dbpath=True).append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(
                    Node, descendant_of='anc',  filters={'id':n8.pk}, edge_tag='edge'
                )
            qb.add_projection('edge', 'depth')
            self.assertTrue(set(zip(*qb.all())[0]), set([5,6]))
            qb.add_filter('edge', {'depth':6})
            self.assertTrue(set(zip(*qb.all())[0]), set([6]))



class TestConsistency(AiidaTestCase):
    def test_create_node_and_query(self):
        from aiida.orm import Node
        from aiida.orm.querybuilder import QueryBuilder


        import random


        for i in range(100):
            n = Node()
            n.store()

        for idx, item in enumerate(QueryBuilder().append(Node,project=['id','label']).iterall(batch_size=10)):
            if idx % 10 == 10:
                print "creating new node"
                n = Node()
                n.store()
        self.assertEqual(idx,99)
        self.assertTrue(len(QueryBuilder().append(Node,project=['id','label']).all(batch_size=10)) > 99)



