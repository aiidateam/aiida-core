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



class QueryBuilderPathSQLA(SqlAlchemyTests):
    def test_query_path(self):

        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node

        n1 = Node()
        n1.store()
        n2 = Node()
        n2.store()
        n3 = Node()
        n3.store()
        n4 = Node()
        n4.store()
        n5 = Node()
        n5.store()
        n6 = Node()
        n6.store()
        n7 = Node()
        n7.store()
        n8 = Node()
        n8.store()
        n9 = Node()
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

        # Yet, no links from 1 to 8
        self.assertEquals(
                QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                ).count(), 0)
        
        self.assertEquals(
                QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of_beta='anc',  filters={'id':n8.pk}
                ).count(), 0)

        self.assertEquals(
                QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                ).count(), 0)
        self.assertEquals(
                QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of_beta='desc',  filters={'id':n1.pk}
                ).count(), 0)
        
        
        
        n6.add_link_from(n5)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                ).count(), 2
            )
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of_beta='anc',  filters={'id':n8.pk}
                ).count(), 2
            )
        self.assertEquals(
                QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                ).count(), 2)
        self.assertEquals(
                QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of_beta='desc',  filters={'id':n1.pk}
                ).count(), 2)

        n7.add_link_from(n9)
        # Still two links...
        
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                ).count(), 2
            )

        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of_beta='anc',  filters={'id':n8.pk}
                ).count(), 2
            )
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                ).count(), 2)
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of_beta='desc',  filters={'id':n1.pk}
                ).count(), 2)

        n9.add_link_from(n6)
        # And now there should be 4 nodes
        
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of='anc',  filters={'id':n8.pk}
                ).count(), 4)

        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n1.pk}, tag='anc'
                ).append(Node, descendant_of_beta='anc',  filters={'id':n8.pk}
                ).count(), 4)
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of='desc',  filters={'id':n1.pk}
                ).count(), 4)
        self.assertEquals(
            QueryBuilder().append(
                    Node, filters={'id':n8.pk}, tag='desc'
                ).append(Node, ancestor_of_beta='desc',  filters={'id':n1.pk}
                ).count(), 4)
