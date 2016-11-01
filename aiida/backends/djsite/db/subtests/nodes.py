# -*- coding: utf-8 -*-
"""
Tests for nodes, attributes and links
"""


from aiida.backends.djsite.db.testbase import AiidaTestCase
from aiida.backends.tests.nodes import (
    TestDataNode, TestTransitiveNoLoops, TestTransitiveClosureDeletion,
    TestQueryWithAiidaObjects, TestNodeBasic, TestSubNodesAndLinks)

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


class TestDataNodeDjango(AiidaTestCase, TestDataNode):
    """
    These tests check the features of Data nodes that differ from the base Node
    """
    def test_links_and_queries(self):
        from aiida.backends.djsite.db.models import DbNode, DbLink

        a = Node()
        a._set_attr('myvalue', 123)
        a.store()

        a2 = Node().store()

        a3 = Node()
        a3._set_attr('myvalue', 145)
        a3.store()

        a4 = Node().store()

        a2.add_link_from(a)
        a3.add_link_from(a2)
        a4.add_link_from(a2)
        a4.add_link_from(a3)

        b = Node.query(pk=a2)
        self.assertEquals(len(b), 1)
        # It is a aiida.orm.Node instance
        self.assertTrue(isinstance(b[0], Node))
        self.assertEquals(b[0].uuid, a2.uuid)

        going_out_from_a2 = Node.query(inputs__in=b)
        # Two nodes going out from a2
        self.assertEquals(len(going_out_from_a2), 2)
        self.assertTrue(isinstance(going_out_from_a2[0], Node))
        self.assertTrue(isinstance(going_out_from_a2[1], Node))
        uuid_set = set([going_out_from_a2[0].uuid, going_out_from_a2[1].uuid])

        # I check that I can query also directly the django DbNode
        # class passing a aiida.orm.Node entity

        going_out_from_a2_db = DbNode.objects.filter(inputs__in=b)
        self.assertEquals(len(going_out_from_a2_db), 2)
        self.assertTrue(isinstance(going_out_from_a2_db[0], DbNode))
        self.assertTrue(isinstance(going_out_from_a2_db[1], DbNode))
        uuid_set_db = set([going_out_from_a2_db[0].uuid,
                           going_out_from_a2_db[1].uuid])

        # I check that doing the query with a Node or DbNode instance,
        # I get the same nodes
        self.assertEquals(uuid_set, uuid_set_db)

        # This time I don't use the __in filter, but I still pass a Node instance
        going_out_from_a2_bis = Node.query(inputs=b[0])
        self.assertEquals(len(going_out_from_a2_bis), 2)
        self.assertTrue(isinstance(going_out_from_a2_bis[0], Node))
        self.assertTrue(isinstance(going_out_from_a2_bis[1], Node))

        # Query for links starting from b[0]==a2 using again the Node class
        output_links_b = DbLink.objects.filter(input=b[0])
        self.assertEquals(len(output_links_b), 2)
        self.assertTrue(isinstance(output_links_b[0], DbLink))
        self.assertTrue(isinstance(output_links_b[1], DbLink))
        uuid_set_db_link = set([output_links_b[0].output.uuid,
                                output_links_b[1].output.uuid])
        self.assertEquals(uuid_set, uuid_set_db_link)

        # Query for related fields using django syntax
        # Note that being myvalue an attribute, it is internally stored starting
        # with an underscore
        nodes_with_given_attribute = Node.query(dbattributes__key='myvalue',
                                                dbattributes__ival=145)
        # should be entry a3
        self.assertEquals(len(nodes_with_given_attribute), 1)
        self.assertTrue(isinstance(nodes_with_given_attribute[0], Node))
        self.assertEquals(nodes_with_given_attribute[0].uuid, a3.uuid)


class TestTransitiveNoLoopsDjango(AiidaTestCase, TestTransitiveNoLoops):
    """
    Test the creation of the transitive closure table
    """
    pass


class TestTransitiveClosureDeletionDjango(AiidaTestCase, TestTransitiveClosureDeletion):
    def test_creation_and_deletion(self):
        from aiida.backends.djsite.db.models import DbLink  # Direct links
        from aiida.backends.djsite.db.models import \
            DbPath  # The transitive closure table
        from aiida.orm.node import Node

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()
        n6 = Node().store()
        n7 = Node().store()
        n8 = Node().store()
        n9 = Node().store()

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
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 0)

        n6.add_link_from(n5)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 2)

        n7.add_link_from(n9)
        # Still two links...
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 2)

        n9.add_link_from(n6)
        # And now there should be 4 nodes
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 4)

        ### I start deleting now

        # I cut one branch below: I should loose 2 links
        DbLink.objects.filter(input=n6, output=n9).delete()
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 2)

        # print "\n".join([str((i.pk, i.input.pk, i.output.pk))
        #                 for i in DbLink.objects.filter()])
        # print "\n".join([str((i.pk, i.parent.pk, i.child.pk, i.depth,
        #                      i.entry_edge_id, i.direct_edge_id,
        #                      i.exit_edge_id)) for i in DbPath.objects.filter()])

        # I cut another branch above: I should loose one more link
        DbLink.objects.filter(input=n2, output=n4).delete()
        # print "\n".join([str((i.pk, i.input.pk, i.output.pk))
        #                 for i in DbLink.objects.filter()])
        # print "\n".join([str((i.pk, i.parent.pk, i.child.pk, i.depth,
        #                      i.entry_edge_id, i.direct_edge_id,
        #                      i.exit_edge_id)) for i in DbPath.objects.filter()])
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 1)

        # Another cut should delete all links
        DbLink.objects.filter(input=n3, output=n5).delete()
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 0)

        # But I did not delete everything! For instance, I can check
        # the following links
        self.assertEquals(
            len(DbPath.objects.filter(parent=n4, child=n8).distinct()), 1)
        self.assertEquals(
            len(DbPath.objects.filter(parent=n5, child=n7).distinct()), 1)

        # Finally, I reconnect in a different way the two graphs and
        # check that 1 and 8 are again connected
        n4.add_link_from(n3)
        self.assertEquals(
            len(DbPath.objects.filter(parent=n1, child=n8).distinct()), 1)




class TestQueryWithAiidaObjectsDjango(AiidaTestCase, TestQueryWithAiidaObjects):
    pass


class TestNodeBasicDango(AiidaTestCase, TestNodeBasic):
    pass


class TestSubNodesAndLinksDjango(AiidaTestCase, TestSubNodesAndLinks):
    pass