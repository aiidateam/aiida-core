from aiida.backends.tests.query import TestQueryBuilder, QueryBuilderJoinsTests
from aiida.backends.sqlalchemy.tests.testbase import SqlAlchemyTests


class TestQueryBuilderSQLA(SqlAlchemyTests, TestQueryBuilder):
    def test_clsf_sqla(self):
        from aiida.orm import Group, User, Computer, Node, Data, Calculation
        from aiida.backends.sqlalchemy.models.node import DbNode
        from aiida.backends.sqlalchemy.models.group import DbGroup
        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.backends.sqlalchemy.models.computer import DbComputer
         
        from aiida.orm.querybuilder import QueryBuilder
        
        qb = QueryBuilder()
        for AiidaCls, ORMCls, typestr in zip(
                (Group, User, Computer, Node, Data, Calculation),
                (DbGroup, DbUser, DbComputer, DbNode, DbNode, DbNode),
                (None, None, None, Node._query_type_string, Data._query_type_string, Calculation._query_type_string)):
            
            cls, clstype, query_type_string = qb._get_ormclass(AiidaCls, None)
            
            
            self.assertEqual(cls, ORMCls)
            self.assertEqual(query_type_string, typestr)



class QueryBuilderJoinsTestsSQLA(SqlAlchemyTests, QueryBuilderJoinsTests):
    pass
