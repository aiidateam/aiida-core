# -*- coding: utf-8 -*-




__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

def is_postgres():
    from aiida.backends import settings
    from aiida.common.setup import get_profile_config
    profile_conf = get_profile_config(settings.AIIDADB_PROFILE)
    return profile_conf['AIIDADB_ENGINE'] == 'postgresql_psycopg2'


def is_django():
    from aiida.backends import settings
    return settings.BACKEND == 'django'

class TestQueryBuilder():

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


    #~ @unittest.skipIf(not (is_django()), "Tests only works with Django backend")
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
