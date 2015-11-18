# -*- coding: utf-8 -*-

import unittest


from sqlalchemy.exc import SQLAlchemyError


from aiida.backends.sqlalchemy.models.node import DbLink, DbPath
from aiida.backends.sqlalchemy.tests.base import SqlAlchemyTests

from aiida.orm.node import Node
from aiida.orm import JobCalculation, CalculationFactory, Data, DataFactory


class TestTransitive(SqlAlchemyTests):

    def test_loop_not_allowed(self):
        """
        Test that no loop can be formed when inserting link
        """
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        n2._add_link_from(n1)
        n3._add_link_from(n2)
        n4._add_link_from(n3)

        with self.assertRaises(ValueError):  # This would generate a loop
            n1._add_link_from(n4)

    def test_creation_and_deletion(self):
        """
        Test the creation and deletion of the transitive closure table
        """

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
        n3._add_link_from(n2)
        n2._add_link_from(n1)
        n5._add_link_from(n3)
        n5._add_link_from(n4)
        n4._add_link_from(n2)

        n7._add_link_from(n6)
        n8._add_link_from(n7)

        # Yet, no links from 1 to 8
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 0)

        n6._add_link_from(n5)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 2)

        n7._add_link_from(n9)
        # Still two links...
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 2)

        n9._add_link_from(n6)
        # And now there should be 4 nodes
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 4)

        ### I start deleting now

        # I cut one branch below: I should loose 2 links
        self.session.delete(DbLink.query.filter_by(input_id=n6.dbnode.id,
                                                     output_id=n9.dbnode.id).first())
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 2)


        # I cut another branch above: I should loose one more link
        self.session.delete(DbLink.query.filter_by(input_id=n2.dbnode.id,
                                                     output_id=n4.dbnode.id).first())

        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)

        # Another cut should delete all links
        self.session.delete(DbLink.query.filter_by(input_id=n3.dbnode.id,
                                                     output_id=n5.dbnode.id).first())

        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 0)

        # But I did not delete everything! For instance, I can check
        # the following links
        self.assertEquals(DbPath.query.filter_by(parent_id=n4.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)
        self.assertEquals(DbPath.query.filter_by(parent_id=n5.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)

        # Finally, I reconnect in a different way the two graphs and
        # check that 1 and 8 are again connected
        n4._add_link_from(n3)
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)

class TestQueryWithAiidaObjects(SqlAlchemyTests):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.backends.sqlalchemy.models.node.DbNode objects.
    """

    @SqlAlchemyTests.inject_computer
    def test_with_subclasses(self, computer):

        extra_name = self.__class__.__name__ + "/test_with_subclasses"
        calc_params = {
            'computer': computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        TemplateReplacerCalc = CalculationFactory('simpleplugins.templatereplacer')
        ParameterData = DataFactory('parameter')

        a1 = JobCalculation(**calc_params).store()
        # To query only these nodes later
        a1.set_extra(extra_name, True)
        a2 = TemplateReplacerCalc(**calc_params).store()
        # To query only these nodes later
        a2.set_extra(extra_name, True)
        a3 = Data().store()
        a3.set_extra(extra_name, True)
        a4 = ParameterData(dict={'a': 'b'}).store()
        a4.set_extra(extra_name, True)
        a5 = Node().store()
        a5.set_extra(extra_name, True)
        # I don't set the extras, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = JobCalculation(**calc_params)
        a6.store()
        a7 = Node()
        a7.store()

        # Query by calculation
        results = list(JobCalculation.query(dbextras__key=extra_name))
        # a3, a4, a5 should not be found because they are not JobCalculations.
        # a6, a7 should not be found because they have not the attribute set.
        self.assertEquals(set([i.pk for i in results]),
                          set([a1.pk, a2.pk]))

        # Same query, but by the generic Node class
        results = list(Node.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a1.pk, a2.pk, a3.pk, a4.pk, a5.pk]))

        # Same query, but by the Data class
        results = list(Data.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a3.pk, a4.pk]))

        # Same query, but by the ParameterData subclass
        results = list(ParameterData.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a4.pk]))

        # Same query, but by the TemplateReplacerCalc subclass
        results = list(TemplateReplacerCalc.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a2.pk]))


    def test_get_inputs_and_outputs(self):
        a1 = Node().store()
        a2 = Node().store()
        a3 = Node().store()
        a4 = Node().store()

        a2._add_link_from(a1)
        a3._add_link_from(a2)
        a4._add_link_from(a2)
        a4._add_link_from(a3)

        # I check that I get the correct links
        self.assertEquals(set([n.uuid for n in a1.get_inputs()]),
                          set([]))
        self.assertEquals(set([n.uuid for n in a1.get_outputs()]),
                          set([a2.uuid]))

        self.assertEquals(set([n.uuid for n in a2.get_inputs()]),
                          set([a1.uuid]))
        self.assertEquals(set([n.uuid for n in a2.get_outputs()]),
                          set([a3.uuid, a4.uuid]))

        self.assertEquals(set([n.uuid for n in a3.get_inputs()]),
                          set([a2.uuid]))
        self.assertEquals(set([n.uuid for n in a3.get_outputs()]),
                          set([a4.uuid]))

        self.assertEquals(set([n.uuid for n in a4.get_inputs()]),
                          set([a2.uuid, a3.uuid]))
        self.assertEquals(set([n.uuid for n in a4.get_outputs()]),
                          set([]))

    @unittest.skip("")
    def test_links_and_queries(self):
        a = Node()
        a._set_attr('myvalue', 123)
        a.store()

        a2 = Node().store()

        a3 = Node()
        a3._set_attr('myvalue', 145)
        a3.store()

        a4 = Node().store()

        a2._add_link_from(a)
        a3._add_link_from(a2)
        a4._add_link_from(a2)
        a4._add_link_from(a3)

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
