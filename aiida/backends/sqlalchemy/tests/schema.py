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
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.orm.node import Node
from aiida.orm.querybuilder import QueryBuilder
import aiida

from aiida.common.utils import get_new_uuid


class TestRelationshipsSQLA(AiidaTestCase):
    """
    Class of tests concerning the schema and the correct
    implementation of relationships within the AiiDA ORM

    The genereal naming convention is the following:
    1)tests on one-to-many relationships: test_<Parent>_<child> (Parent class is capitalized)
    2)tests on many-to-many relationships: test_<peer>_<peer> (none is
    capitalized)


    """

    def test_outputs_children_relationship(self):
        """
        This test checks that the outputs_q, children_q relationship and the
        corresponding properties work as expected.
        """
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()

        # Create a link between these 2 nodes
        n2.add_link_from(n1, "N1")
        n3.add_link_from(n2, "N2")

        # Check that the result of outputs is a list
        self.assertIsInstance(n1.dbnode.outputs, list,
                              "This is expected to be a list")

        # Check that the result of outputs_q is a query
        from sqlalchemy.orm.dynamic import AppenderQuery
        self.assertIsInstance(n1.dbnode.outputs_q, AppenderQuery,
                              "This is expected to be an AppenderQuery")

        # Check that the result of children is a list
        self.assertIsInstance(n1.dbnode.children, list,
                              "This is expected to be a list")

        # Check that the result of children_q is a list
        from sqlalchemy.orm.dynamic import AppenderQuery
        self.assertIsInstance(n1.dbnode.children_q, AppenderQuery,
                              "This is expected to be an AppenderQuery")

        # Check that the result of outputs is correct
        out = set([_.pk for _ in n1.dbnode.outputs])
        self.assertEqual(out, set([n2.pk]))

        # Check that the result of children is correct
        out = set([_.pk for _ in n1.dbnode.children])
        self.assertEqual(out, set([n2.pk, n3.pk]))

    def test_inputs_parents_relationship(self):
        """
        This test checks that the inputs_q, parents_q relationship and the
        corresponding properties work as expected.
        """
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()

        # Create a link between these 2 nodes
        n2.add_link_from(n1, "N1")
        n3.add_link_from(n2, "N2")

        # Check that the result of outputs is a list
        self.assertIsInstance(n1.dbnode.inputs, list,
                              "This is expected to be a list")

        # Check that the result of outputs_q is a query
        from sqlalchemy.orm.dynamic import AppenderQuery
        self.assertIsInstance(n1.dbnode.inputs_q, AppenderQuery,
                              "This is expected to be an AppenderQuery")

        # Check that the result of children is a list
        self.assertIsInstance(n1.dbnode.parents, list,
                              "This is expected to be a list")

        # Check that the result of children_q is a list
        from sqlalchemy.orm.dynamic import AppenderQuery
        self.assertIsInstance(n1.dbnode.parents_q, AppenderQuery,
                              "This is expected to be an AppenderQuery")

        # Check that the result of inputs is correct
        out = set([_.pk for _ in n3.dbnode.inputs])
        self.assertEqual(out, set([n2.pk]))

        # Check that the result of parents is correct
        out = set([_.pk for _ in n3.dbnode.parents])
        self.assertEqual(out, set([n1.pk, n2.pk]))

    def test_User_node_1(self):
        """
        Test that when a user and a node having that user are created,
        storing NODE induces storage of the USER

        Assert the correct storage of user and node

        """

        # Create user
        dbu1 = DbUser('test1@schema', "spam", "eggs",
               "monty")

        # Creat node
        node_dict = dict(user=dbu1)
        dbn1 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn1.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()
        # Add only the node and commit
        session.add(dbn1)
        session.commit()

        # Check that a pk has been assigned, which means that things have
        # been flushed into the database
        self.assertIsNotNone(dbn1.id)
        self.assertIsNotNone(dbu1.id)

    def test_User_node_2(self):
        """
        Test that when a user and a node having that user are created,
        storing USER does NOT induce storage of the NODE

        Assert the correct storage of user and node

        """
        import warnings
        from sqlalchemy import exc as sa_exc

        # Create user
        dbu1 = DbUser('tests2@schema', "spam", "eggs",
               "monty")

        # Creat node
        node_dict = dict(user=dbu1)
        dbn1 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn1.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Catch all the SQLAlchemy warnings generated by the following code
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=sa_exc.SAWarning)

            # Add only the user and commit
            session.add(dbu1)
            session.commit()

        # Check that a pk has been assigned (or not), which means that things
        # have been flushed into the database
        self.assertIsNotNone(dbu1.id)
        self.assertIsNone(dbn1.id)

    def test_User_node_3(self):
        """
        Test that when a user and two nodes having that user are created,
        storing only ONE NODE induces storage of that node, of the user but
        not of the other node

        Assert the correct storage of the user and node. Assert the
        non-storage of the other node

        """
        # Create user
        dbu1 = DbUser('tests3@schema', "spam", "eggs",
               "monty")

        # Creat node
        node_dict = dict(user=dbu1)
        dbn1 = DbNode(**node_dict)
        dbn2 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn1.id)
        self.assertIsNone(dbn2.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Add only first node and commit
        session.add(dbn1)
        session.commit()

        # Check for which object a pk has been assigned, which means that
        # things have been at least flushed into the database
        self.assertIsNotNone(dbu1.id)
        self.assertIsNotNone(dbn1.id)
        self.assertIsNone(dbn2.id)

    def test_User_node_4(self):
        """
        Test that when several nodes are created with the same user and each
        of them is assigned to the same name, storage of last node object
        associated to that node does not trigger storage of all objects.


        Assert the correct storage of the user and node. Assert the
        non-storage of the other nodes
        """
        # Create user
        dbu1 = DbUser('tests4@schema', "spam", "eggs",
               "monty")

        # Creat node objects assigningd them to the same name
        # Check https://docs.python.org/2/tutorial/classes.html subsec. 9.1

        for _ in range(5):
            # It is important to change the uuid each time (or any other
            # variable) so that a different objects (with a different pointer)
            # is actually created in this scope.
            dbn1 = DbNode(user=dbu1, uuid=get_new_uuid())

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn1.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Add only first node and commit
        session.add(dbn1)
        session.commit()

        # Check for which object a pk has been assigned, which means that
        # things have been at least flushed into the database
        self.assertIsNotNone(dbu1.id)
        self.assertIsNotNone(dbn1.id)

        # # Check that only one stored node has user_id equal to that of dbu1
        # qb = QueryBuilder()
        # qb.append(Node, filters={'user_id': {'==', dbu1.id}})
        # self.assertIs(qb.count(), 1)


    # def test_Computer_node_1(self):
    #     """
    #     Test that when a user and a node having that user are created,
    #     storing NODE induces storage of the COMPUTER
    #
    #     Assert the correct storage of user and node
    #
    #     """
    #
    #     # Create computer
    #     dbc1 = DbComputer(name='test1')
    #
    #     # Creat node
    #     node_dict = dict(dbcomputer=dbc1)
    #     dbn1 = DbNode(**node_dict)
    #
    #     # Check that the two are neither flushed nor committed
    #     self.assertIsNone(dbc1.id)
    #     self.assertIsNone(dbn1.id)
    #
    #     # Add only the node and commit
    #     aiida.backends.sqlalchemy.get_scoped_session().add(dbn1)
    #     aiida.backends.sqlalchemy.get_scoped_session().commit()
    #
    #     # Check that a pk has been assigned, which means that things have
    #     # been flushed into the database
    #     self.assertIsNotNone(dbn1.id)
    #     self.assertIsNotNone(dbc1.id)
    #
    #
    # def test_Computer_node_2(self):
    #     """
    #     Test that when a user and a node having that user are created,
    #     storing COMPUTER does NOT induce storage of the NODE
    #
    #     Assert the correct storage of user and node
    #
    #     """
    #
    #     # Create computer
    #     dbc1 = DbComputer(name='test2')
    #
    #     # Creat node
    #     node_dict = dict(dbcomputer=dbc1)
    #     dbn1 = DbNode(**node_dict)
    #
    #     # Check that the two are neither flushed nor committed
    #     self.assertIsNone(dbc1.id)
    #     self.assertIsNone(dbn1.id)
    #
    #     # Add only the user and commit
    #     aiida.backends.sqlalchemy.get_scoped_session().add(dbc1)
    #     aiida.backends.sqlalchemy.get_scoped_session().commit()
    #
    #     # Check that a pk has been assigned (or not), which means that things
    #     # have been flushed into the database
    #     self.assertIsNotNone(dbc1.id)
    #     self.assertIsNone(dbn1.id)
    #
    #
    # def test_Computer_node_3(self):
    #     """
    #     Test that when a user and two nodes having that user are created,
    #     storing only ONE NODE induces storage of that node, of the computer but
    #     not of the other node
    #
    #     Assert the correct storage of the user and node. Assert the
    #     non-storage of the other node
    #
    #     """
    #     # Create computer
    #     dbc1 = DbComputer(name='test3')
    #
    #     # Creat node
    #     node_dict = dict(dbcomputer=dbc1)
    #     dbn1 = DbNode(**node_dict)
    #     dbn2 = DbNode(**node_dict)
    #
    #     # Check that the two are neither flushed nor committed
    #     self.assertIsNone(dbc1.id)
    #     self.assertIsNone(dbn1.id)
    #     self.assertIsNone(dbn2.id)
    #
    #     # Add only first node and commit
    #     aiida.backends.sqlalchemy.get_scoped_session().add(dbn1)
    #     aiida.backends.sqlalchemy.get_scoped_session().commit()
    #
    #     # Check for which object a pk has been assigned, which means that
    #     # things have been at least flushed into the database
    #     self.assertIsNotNone(dbc1.id)
    #     self.assertIsNotNone(dbn1.id)
    #     self.assertIsNone(dbn2.id)
    #
    #
    # def test_Computer_node_4(self):
    #     """
    #     Test that when several nodes are created with the same computer and each
    #     of them is assigned to the same name, storage of last node object
    #     associated to that node does not trigger storage of all objects.
    #
    #
    #     Assert the correct storage of the user and node. Assert the
    #     non-storage of the other nodes
    #     """
    #
    #     # Create computer
    #     dbc1 = DbComputer(name='test4')
    #
    #     # Creat node objects assigningd them to the same name
    #     # Check https://docs.python.org/2/tutorial/classes.html subsec. 9.1
    #
    #     for _ in range(5):
    #         # It is important to change the uuid each time (or any other
    #         # variable) so that a different objects (with a different pointer)
    #         # is actually created in this scope.
    #         dbn1 = DbNode(dbcomputer=dbc1, uuid=get_new_uuid())
    #
    #     # Check that the two are neither flushed nor committed
    #     self.assertIsNone(dbc1.id)
    #     self.assertIsNone(dbn1.id)
    #
    #     # Add only first node and commit
    #     aiida.backends.sqlalchemy.get_scoped_session().add(dbn1)
    #     aiida.backends.sqlalchemy.get_scoped_session().commit()
    #
    #     # Check for which object a pk has been assigned, which means that
    #     # things have been at least flushed into the database
    #     self.assertIsNotNone(dbc1.id)
    #     self.assertIsNotNone(dbn1.id)
    #
    #     #
    #     # # Check that only one stored node has user_id equal to that of dbu1
    #     # qb = QueryBuilder()
    #     # qb.append(Node, filters={'computer_id': {'==', dbc1.id}})
    #     # self.assertIs(qb.count(), 1)