###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test object relationships in the database."""

import warnings

from sqlalchemy import exc as sa_exc

from aiida.common.links import LinkType
from aiida.common.utils import get_new_uuid
from aiida.manage import get_manager
from aiida.orm import CalculationNode, Data
from aiida.storage.psql_dos.models.node import DbNode
from aiida.storage.psql_dos.models.user import DbUser


class TestRelationshipsSQLA:
    """Class of tests concerning the schema and the correct
    implementation of relationships within the AiiDA ORM

    The genereal naming convention is the following:
    1)tests on one-to-many relationships: test_<Parent>_<child> (Parent class is capitalized).
    2)tests on many-to-many relationships: test_<peer>_<peer> (none is
    capitalized).
    """

    def test_outputs_children_relationship(self):
        """This test checks that the outputs_q, children_q relationship and the
        corresponding properties work as expected.
        """
        n_1 = Data().store()
        n_2 = CalculationNode()
        n_3 = Data().store()

        # Create a link between these 2 nodes
        n_2.base.links.add_incoming(n_1, link_type=LinkType.INPUT_CALC, link_label='N1')
        n_2.store()
        n_3.base.links.add_incoming(n_2, link_type=LinkType.CREATE, link_label='N2')

        # Check that the result of outputs is a list
        assert isinstance(n_1.backend_entity.bare_model.outputs, list), 'This is expected to be a list'

        # Check that the result of outputs_q is a query
        from sqlalchemy.orm.dynamic import AppenderQuery

        assert isinstance(
            n_1.backend_entity.bare_model.outputs_q, AppenderQuery
        ), 'This is expected to be an AppenderQuery'

        # Check that the result of outputs is correct
        out = {_.pk for _ in n_1.backend_entity.bare_model.outputs}
        assert out == set([n_2.pk])

    def test_inputs_parents_relationship(self):
        """This test checks that the inputs_q, parents_q relationship and the
        corresponding properties work as expected.
        """
        n_1 = Data().store()
        n_2 = CalculationNode()
        n_3 = Data().store()

        # Create a link between these 2 nodes
        n_2.base.links.add_incoming(n_1, link_type=LinkType.INPUT_CALC, link_label='N1')
        n_2.store()
        n_3.base.links.add_incoming(n_2, link_type=LinkType.CREATE, link_label='N2')

        # Check that the result of outputs is a list
        assert isinstance(n_1.backend_entity.bare_model.inputs, list), 'This is expected to be a list'

        # Check that the result of outputs_q is a query
        from sqlalchemy.orm.dynamic import AppenderQuery

        assert isinstance(
            n_1.backend_entity.bare_model.inputs_q, AppenderQuery
        ), 'This is expected to be an AppenderQuery'

        # Check that the result of inputs is correct
        out = {_.pk for _ in n_3.backend_entity.bare_model.inputs}
        assert out == set([n_2.pk])

    def test_user_node_1(self):
        """Test that when a user and a node having that user are created,
        storing NODE induces storage of the USER

        Assert the correct storage of user and node.
        """
        # Create user
        dbu1 = DbUser(email='test1@schema', first_name='spam', last_name='eggs', institution='monty')

        # Creat node
        node_dict = dict(user=dbu1)
        dbn_1 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        assert dbu1.id is None
        assert dbn_1.id is None

        session = get_manager().get_profile_storage().get_session()
        # Add only the node and commit
        session.add(dbn_1)
        session.commit()

        # Check that a pk has been assigned, which means that things have
        # been flushed into the database
        assert dbn_1.id is not None
        assert dbu1.id is not None

    def test_user_node_2(self):
        """Test that when a user and a node having that user are created,
        storing USER does NOT induce storage of the NODE

        Assert the correct storage of user and node.
        """
        # Create user
        dbu1 = DbUser(email='test2@schema', first_name='spam', last_name='eggs', institution='monty')

        # Creat node
        node_dict = dict(user=dbu1)
        dbn_1 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        assert dbu1.id is None
        assert dbn_1.id is None

        session = get_manager().get_profile_storage().get_session()

        # Catch all the SQLAlchemy warnings generated by the following code
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)

            # Add only the user and commit
            session.add(dbu1)
            session.commit()

        # Check that a pk has been assigned (or not), which means that things
        # have been flushed into the database
        assert dbu1.id is not None
        assert dbn_1.id is None

    def test_user_node_3(self):
        """Test that when a user and two nodes having that user are created,
        storing only ONE NODE induces storage of that node, of the user but
        not of the other node

        Assert the correct storage of the user and node. Assert the
        non-storage of the other node.
        """
        # Create user
        dbu1 = DbUser(email='test3@schema', first_name='spam', last_name='eggs', institution='monty')

        # Creat node
        node_dict = dict(user=dbu1)
        dbn_1 = DbNode(**node_dict)
        dbn_2 = DbNode(**node_dict)

        # Check that the two are neither flushed nor committed
        assert dbu1.id is None
        assert dbn_1.id is None
        assert dbn_2.id is None

        session = get_manager().get_profile_storage().get_session()

        # Add only first node and commit
        session.add(dbn_1)
        with warnings.catch_warnings():
            # suppress known SAWarning that we have not added dbn_2
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            session.commit()

        # Check for which object a pk has been assigned, which means that
        # things have been at least flushed into the database
        assert dbu1.id is not None
        assert dbn_1.id is not None
        assert dbn_2.id is None

    def test_user_node_4(self):
        """Test that when several nodes are created with the same user and each
        of them is assigned to the same name, storage of last node object
        associated to that node does not trigger storage of all objects.


        Assert the correct storage of the user and node. Assert the
        non-storage of the other nodes.
        """
        # Create user
        dbu1 = DbUser(email='test4@schema', first_name='spam', last_name='eggs', institution='monty')

        # Creat node objects assigningd them to the same name
        # Check https://docs.python.org/2/tutorial/classes.html subsec. 9.1

        for _ in range(5):
            # It is important to change the uuid each time (or any other
            # variable) so that a different objects (with a different pointer)
            # is actually created in this scope.
            dbn_1 = DbNode(user=dbu1, uuid=get_new_uuid())

        # Check that the two are neither flushed nor committed
        assert dbu1.id is None
        assert dbn_1.id is None

        session = get_manager().get_profile_storage().get_session()

        # Add only first node and commit
        session.add(dbn_1)
        with warnings.catch_warnings():
            # suppress known SAWarning that we have not add the other nodes
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            session.commit()

        # Check for which object a pk has been assigned, which means that
        # things have been at least flushed into the database
        assert dbu1.id is not None
        assert dbn_1.id is not None
