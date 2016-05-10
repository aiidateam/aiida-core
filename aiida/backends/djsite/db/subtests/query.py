from aiida.backends.djsite.db.testbase import AiidaTestCase
from django.utils import unittest


def is_postgres():
    from aiida.backends import settings
    from aiida.common.setup import get_profile_config
    profile_conf = get_profile_config(settings.AIIDADB_PROFILE)
    return profile_conf['AIIDADB_ENGINE'] == 'postgresql_psycopg2'

class TestQueryBuilder(AiidaTestCase):
    def test_querybuilder_classifications_django(self):
        from aiida.backends.querybuild.querybuilder_django import QueryBuilder
        from aiida.backends.querybuild.dummy_model import (
                DbNode, DbUser, DbComputer,
                DbGroup,
            )
        from aiida.orm.utils import (DataFactory, CalculationFactory)
        from aiida.orm.data.structure import StructureData
        from aiida.orm.implementation.django.node import Node
        
        qb = QueryBuilder()
        
        cls, clstype = qb._get_ormclass(DataFactory('structure'), None)
        self.assertEqual(clstype, 'data.structure.StructureData.')
        self.assertTrue(issubclass(cls, DbNode))

        cls, clstype = qb._get_ormclass(None, 'structure')
        self.assertEqual(clstype, 'data.structure.StructureData.')
        self.assertTrue(issubclass(cls, DbNode))

        cls, clstype = qb._get_ormclass(Node, None)
        self.assertEqual(clstype, 'node.Node')
        self.assertTrue(issubclass(cls, DbNode))

        cls, clstype = qb._get_ormclass(DbNode, None)
        self.assertEqual(clstype, 'node.Node')
        self.assertTrue(issubclass(cls, DbNode))

        cls, clstype = qb._get_ormclass(None, 'node')
        self.assertEqual(clstype, 'node.Node')
        self.assertTrue(issubclass(cls, DbNode))

        cls, clstype = qb._get_ormclass(DbGroup, None)
        self.assertEqual(clstype, 'group')
        self.assertTrue(issubclass(cls, DbGroup))

        cls, clstype = qb._get_ormclass(None, 'group')
        self.assertEqual(clstype, 'group')
        self.assertTrue(issubclass(cls, DbGroup))

        cls, clstype = qb._get_ormclass(DbUser, None)
        self.assertEqual(clstype, 'user')
        self.assertTrue(issubclass(cls, DbUser))

        cls, clstype = qb._get_ormclass(None, "user")
        self.assertEqual(clstype, 'user')
        self.assertTrue(issubclass(cls, DbUser))

        cls, clstype = qb._get_ormclass(DbComputer, None)
        self.assertEqual(clstype, 'computer')
        self.assertTrue(issubclass(cls, DbComputer))

        cls, clstype = qb._get_ormclass(None, "computer"    )
        self.assertEqual(clstype, 'computer')
        self.assertTrue(issubclass(cls, DbComputer))

    @unittest.skipIf(not is_postgres(), "Tests only works with postgres")
    def test_simple_query_django(self):
        """
        Testing a simple query
        """
        from aiida.backends.querybuild.querybuilder_django import QueryBuilder
        from aiida.backends.querybuild.dummy_model import (
                DbNode, DbLink, session, Base, DbAttribute, DbUser
            )
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm import Node
        from datetime import datetime

        n0 = DbNode(
                label='hello',
                type='tester.TesterData.',
                description='', user_id=1,
            )
        n1 = DbNode(
                label='foo',
                type='tester.TesterData.FOO',
                description='I am FoO', user_id=2,
            )
        n2 = DbNode(
                label='bar',
                type='tester.TesterData.BAR',
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
        session.flush() # This is not writing to the DB

        qb1 = QueryBuilder()
        qb1.append(
            DbNode,
            filters={
                'label':'hello',
                'type':{'like':'tester%'}
            }
        )
        self.assertEqual(len(qb1.all()),1)

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
                        'type':{'like':'tester.%'},
                        'label':{'ilike':'%foO%'},
                    },
                    'n2':{
                        'type':{'ilike':'tester.%'},
                    }
                },
                'project':{
                    'n1':['id', 'uuid', 'ctime'],
                    'n2':['id', 'description', 'label'],
                }
            }

        qb2 = QueryBuilder(**qh)

        resdict = list(qb2.get_results_dict())
        self.assertEqual(len(resdict),1 )
        resdict = resdict[0]
        self.assertTrue(isinstance(resdict['n1']['ctime'], datetime))
        self.assertEqual(resdict['n2']['label'], 'bar')

        qh['filters']['n1']['label'] = {'like':'%FoO'} # Case sensitive
        qb3 = QueryBuilder(**qh)
        self.assertEqual(len(list(qb3.all())), 0)

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
                    '<>n2':{label:{'like':'%_2'}}
                }
            }
        qb = QueryBuilder(**qh)
        self.assertEqual(len(list(qb.all())), 1)
