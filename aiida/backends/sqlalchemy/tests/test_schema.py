# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Test object relationships in the database."""
from aiida.backends.testbase import AiidaTestCase
from aiida.backends.sqlalchemy.models.user import DbUser
from aiida.backends.sqlalchemy.models.node import DbNode
from aiida.common.links import LinkType
from aiida.orm import Data
from aiida.orm import CalculationNode
import aiida

from aiida.common.utils import get_new_uuid


class TestRelationshipsSQLA(AiidaTestCase):
    """Class of tests concerning the schema and the correct
    implementation of relationships within the AiiDA ORM

    The genereal naming convention is the following:
    1)tests on one-to-many relationships: test_<Parent>_<child> (Parent class is capitalized).
    2)tests on many-to-many relationships: test_<peer>_<peer> (none is
    capitalized)."""

    def test_outputs_children_relationship(self):
        """This test checks that the outputs_q, children_q relationship and the
        corresponding properties work as expected."""
        n_1 = Data().store()
        n_2 = CalculationNode()
        n_3 = Data().store()

        # Create a link between these 2 nodes
        n_2.add_incoming(n_1, link_type=LinkType.INPUT_CALC, link_label='N1')
        n_2.store()
        n_3.add_incoming(n_2, link_type=LinkType.CREATE, link_label='N2')

        # Check that the result of outputs is a list
        self.assertIsInstance(n_1.backend_entity.dbmodel.outputs, list, 'This is expected to be a list')

        # Check that the result of outputs_q is a query
        from sqlalchemy.orm.dynamic import AppenderQuery
        self.assertIsInstance(
            n_1.backend_entity.dbmodel.outputs_q, AppenderQuery, 'This is expected to be an AppenderQuery'
        )

        # Check that the result of outputs is correct
        out = {_.pk for _ in n_1.backend_entity.dbmodel.outputs}
        self.assertEqual(out, set([n_2.pk]))

    def test_inputs_parents_relationship(self):
        """This test checks that the inputs_q, parents_q relationship and the
        corresponding properties work as expected."""
        n_1 = Data().store()
        n_2 = CalculationNode()
        n_3 = Data().store()

        # Create a link between these 2 nodes
        n_2.add_incoming(n_1, link_type=LinkType.INPUT_CALC, link_label='N1')
        n_2.store()
        n_3.add_incoming(n_2, link_type=LinkType.CREATE, link_label='N2')

        # Check that the result of outputs is a list
        self.assertIsInstance(n_1.backend_entity.dbmodel.inputs, list, 'This is expected to be a list')

        # Check that the result of outputs_q is a query
        from sqlalchemy.orm.dynamic import AppenderQuery
        self.assertIsInstance(
            n_1.backend_entity.dbmodel.inputs_q, AppenderQuery, 'This is expected to be an AppenderQuery'
        )

        # Check that the result of inputs is correct
        out = {_.pk for _ in n_3.backend_entity.dbmodel.inputs}
        self.assertEqual(out, set([n_2.pk]))

    def test_user_node_1(self):
        """Test that when a user and a node having that user are created,
        storing NODE induces storage of the USER

        Assert the correct storage of user and node."""

        # Create user
        dbu1 = DbUser('test1@schema', 'spam', 'eggs', 'monty')

        # Creat node
        node_dict = dict(user=dbu1)
        dbn_1 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn_1.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()
        # Add only the node and commit
        session.add(dbn_1)
        session.commit()

        # Check that a pk has been assigned, which means that things have
        # been flushed into the database
        self.assertIsNotNone(dbn_1.id)
        self.assertIsNotNone(dbu1.id)

    def test_user_node_2(self):
        """Test that when a user and a node having that user are created,
        storing USER does NOT induce storage of the NODE

        Assert the correct storage of user and node."""
        import warnings
        from sqlalchemy import exc as sa_exc

        # Create user
        dbu1 = DbUser('tests2@schema', 'spam', 'eggs', 'monty')

        # Creat node
        node_dict = dict(user=dbu1)
        dbn_1 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn_1.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Catch all the SQLAlchemy warnings generated by the following code
        with warnings.catch_warnings():  # pylint: disable=no-member
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)  # pylint: disable=no-member

            # Add only the user and commit
            session.add(dbu1)
            session.commit()

        # Check that a pk has been assigned (or not), which means that things
        # have been flushed into the database
        self.assertIsNotNone(dbu1.id)
        self.assertIsNone(dbn_1.id)

    def test_user_node_3(self):
        """Test that when a user and two nodes having that user are created,
        storing only ONE NODE induces storage of that node, of the user but
        not of the other node

        Assert the correct storage of the user and node. Assert the
        non-storage of the other node."""
        # Create user
        dbu1 = DbUser('tests3@schema', 'spam', 'eggs', 'monty')

        # Creat node
        node_dict = dict(user=dbu1)
        dbn_1 = DbNode(**node_dict)
        dbn_2 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn_1.id)
        self.assertIsNone(dbn_2.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Add only first node and commit
        session.add(dbn_1)
        session.commit()

        # Check for which object a pk has been assigned, which means that
        # things have been at least flushed into the database
        self.assertIsNotNone(dbu1.id)
        self.assertIsNotNone(dbn_1.id)
        self.assertIsNone(dbn_2.id)

    def test_user_node_4(self):
        """Test that when several nodes are created with the same user and each
        of them is assigned to the same name, storage of last node object
        associated to that node does not trigger storage of all objects.


        Assert the correct storage of the user and node. Assert the
        non-storage of the other nodes."""
        # Create user
        dbu1 = DbUser('tests4@schema', 'spam', 'eggs', 'monty')

        # Creat node objects assigningd them to the same name
        # Check https://docs.python.org/2/tutorial/classes.html subsec. 9.1

        for _ in range(5):
            # It is important to change the uuid each time (or any other
            # variable) so that a different objects (with a different pointer)
            # is actually created in this scope.
            dbn_1 = DbNode(user=dbu1, uuid=get_new_uuid())

        # Check that the two are neither flushed nor committed
        self.assertIsNone(dbu1.id)
        self.assertIsNone(dbn_1.id)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # Add only first node and commit
        session.add(dbn_1)
        session.commit()

        # Check for which object a pk has been assigned, which means that
        # things have been at least flushed into the database
        self.assertIsNotNone(dbu1.id)
        self.assertIsNotNone(dbn_1.id)
