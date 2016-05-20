from aiida.backends.djsite.db.testbase import AiidaTestCase
from django.utils import unittest


def is_postgres():
    from aiida.backends import settings
    from aiida.common.setup import get_profile_config
    profile_conf = get_profile_config(settings.AIIDADB_PROFILE)
    return profile_conf['AIIDADB_ENGINE'] == 'postgresql_psycopg2'

def is_django():
    from aiida.backends import settings
    return settings.BACKEND == 'django'


@unittest.skipIf(not(is_django()), "Tests only works with Django backend")
class TestQueryBuilder(AiidaTestCase):
    def test_querybuilder_classifications(self):
        """
        This tests the classifications of the QueryBuilder u. the django backend.
        """
        from aiida.backends.querybuild.dummy_model import (
                DbNode, DbUser, DbComputer,
                DbGroup,
            )
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.utils import (DataFactory, CalculationFactory)
        from aiida.orm.data.structure import StructureData
        from aiida.orm.implementation.django.node import Node
        from aiida.orm import Group, User, Node, Computer, Data, Calculation

        qb = QueryBuilder()


        for cls, clstype in (
                qb._get_ormclass(DataFactory('structure'), None),
                qb._get_ormclass(None, 'structure'),
                qb._get_ormclass(None, 'structure.StructureData'),
            ):
            self.assertEqual(clstype, 'data.structure.StructureData.')
            self.assertTrue(issubclass(cls, DbNode))
            self.assertEqual(clstype, 'data.structure.StructureData.')



        for cls, clstype in (
                qb._get_ormclass(Node, None),
                qb._get_ormclass(DbNode, None),
                qb._get_ormclass(None, 'node')
            ):
            self.assertEqual(clstype, 'node.Node')
            self.assertTrue(issubclass(cls, DbNode))

        for cls, clstype in (
                qb._get_ormclass(DbGroup, None),
                qb._get_ormclass(Group, None),
                qb._get_ormclass(None, 'group'),
                qb._get_ormclass(None, 'Group'),
            ):

            self.assertEqual(clstype, 'group')
            self.assertTrue(issubclass(cls, DbGroup))


        for cls, clstype in (
                qb._get_ormclass(DbUser, None),
                qb._get_ormclass(DbUser, None),
                qb._get_ormclass(None, "user"),
                qb._get_ormclass(None, "User"),
            ):
            self.assertEqual(clstype, 'user')
            self.assertTrue(issubclass(cls, DbUser))

        for cls, clstype in (
                qb._get_ormclass(DbComputer, None),
                qb._get_ormclass(Computer, None),
                qb._get_ormclass(None, 'computer'),
                qb._get_ormclass(None, 'Computer'),
            ):
            self.assertEqual(clstype, 'computer')
            self.assertTrue(issubclass(cls, DbComputer))

        for cls, clstype in (
                qb._get_ormclass(Data, None),
                qb._get_ormclass(None, 'data'),
            ):
            print clstype

    def test_simple_query_django_1(self):
        """
        Testing a simple query
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm import Node, Data, Calculation
        from datetime import datetime

        n1 = Data()
        n1.label = 'test1_node1'
        n1._set_attr('foo',['hello', 'goodbye'])
        n1.store()

        n2 = Calculation()
        n2.label = 'test1_node2'
        n2._set_attr('foo', 1)
        n2.store()

        n3 = Data()
        n3.label = 'test1_node3'
        n3._set_attr('foo', 1.0000) # Stored as fval
        n3.store()

        n4 = Calculation()
        n4.label = 'test1_node4'
        n4._set_attr('foo', 'bar')
        n4.store()

        n5 = Data()
        n5.label = 'test1_node5'
        n5._set_attr('foo', None)
        n5.store()


        n2._add_link_from(n1)
        n3._add_link_from(n2)

        n4._add_link_from(n3)
        n5._add_link_from(n4)

        qb1 = QueryBuilder()
        qb1.append(Node, filters={'attributes.foo':1.000})

        self.assertEqual(len(list(qb1.all())), 2)

        qb2 = QueryBuilder()
        qb2.append(Data)
        self.assertEqual(qb2.count(), 3)

        qb2 = QueryBuilder()
        qb2.append(type='data.Data')
        self.assertEqual(qb2.count(), 3)





    #~ @unittest.skipIf(not is_postgres(), "Tests only works with postgres")
    def test_simple_query_django_2(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node
        from datetime import datetime
        from aiida.backends.querybuild.dummy_model import (
                DbNode, DbLink, DbAttribute, session
            )
        n0 = DbNode(
                label='hello',
                type='',
                description='', user_id=1,
            )
        n1 = DbNode(
                label='foo',
                type='',
                description='I am FoO', user_id=2,
            )
        n2 = DbNode(
                label='bar',
                type='',
                description='I am BaR', user_id=3,
            )

        DbAttribute(
                key='foo',
                datatype='txt',
                tval='bar',
                dbnode=n0
            )

        l1 = DbLink(input=n0, output=n1, label='random_1')
        l2 = DbLink(input=n1, output=n2, label='random_2')

        session.add_all([n0,n1,n2,l1,l2])
        #~ session.flush() # This is not writing to the DB

        qb1 = QueryBuilder()
        qb1.append(
            DbNode,
            filters={
                'label':'hello',
            }
        )
        self.assertEqual(len(list(qb1.all())),1)

        qh = {
                'path':[
                    {
                        'cls':Node,
                        'label':'n1'
                    },
                    {
                        'cls':Node,
                        'label':'n2',
                        'output_of':'n1'
                    }
                ],
                'filters':{
                    'n1':{
                        'label':{'ilike':'%foO%'},
                    },
                    'n2':{
                        'label':{'ilike':'bar%'},
                    }
                },
                'project':{
                    'n1':['id', 'uuid', 'ctime', 'label'],
                    'n2':['id', 'description', 'label'],
                }
            }

        qb2 = QueryBuilder(**qh)

        resdict = list(qb2.get_results_dict())
        self.assertEqual(len(resdict),1 )
        resdict = resdict[0]
        self.assertTrue(isinstance(resdict['n1']['ctime'], datetime))
        self.assertEqual(resdict['n2']['label'], 'bar')


        qh = {
                'path':[
                    {
                        'cls':Node,
                        'label':'n1'
                    },
                    {
                        'cls':Node,
                        'label':'n2',
                        'output_of':'n1'
                    }
                ],
                'filters':{
                    'n1--n2':{'label':{'like':'%_2'}}
                }
            }
        qb = QueryBuilder(**qh)
        self.assertEqual(len(list(qb.all())), 1)


