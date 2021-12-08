# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module,no-member
"""Testing Session possible problems."""
import pytest
from sqlalchemy.orm import sessionmaker

import aiida.backends
from aiida.backends.utils import create_scoped_session_factory
from aiida.manage.manager import get_manager


class TestSessionSqla:
    """The following tests check that the session works as expected in some
    problematic examples. When a session is initialized with
    expire_on_commit=False allows more permissive behaviour since committed
    objects that remain in the session do not need refresh. The opposite
    happens when expire_on_commit=True.

    Moreover, 2 ways of storing objects are tested, i.e. adding the objects
    manually to the session and committing it & by using the build-in store
    method of the ORM objects.
    """

    @pytest.fixture(autouse=True)
    def init_db(self, aiida_profile, backend):  # pylint: disable=unused-argument
        """Initialize the database."""
        # pylint: disable=attribute-defined-outside-init
        aiida_profile.reset_db(with_user=False)
        self.backend = backend
        self.test_profile = aiida_profile

    @staticmethod
    def set_connection(expire_on_commit=True):
        """Set connection to a database."""
        aiida.backends.sqlalchemy.get_scoped_session().expunge_all()
        aiida.backends.sqlalchemy.SESSION_FACTORY = create_scoped_session_factory(
            aiida.backends.sqlalchemy.ENGINE, expire_on_commit=expire_on_commit
        )

    @staticmethod
    def drop_connection():
        """Drop connection to a database."""
        session = aiida.backends.sqlalchemy.get_scoped_session()
        session.expunge_all()
        session.close()
        aiida.backends.sqlalchemy.SESSION_FACTORY = None

    def test_session_update_and_expiration_1(self):
        """expire_on_commit=True & adding manually and committing
        computer and code objects."""

        self.set_connection(expire_on_commit=True)
        session = aiida.backends.sqlalchemy.get_scoped_session()

        email = get_manager().get_profile().default_user
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(
            label='localhost', hostname='localhost', transport_type='core.local', scheduler_type='core.pbspro'
        )
        computer = self.backend.computers.create(**defaults)
        session.add(computer.dbmodel)
        session.commit()

        node = self.backend.nodes.create(node_type='', user=user).store()
        session.add(node.dbmodel)
        session.commit()

        self.drop_connection()

    def test_session_update_and_expiration_2(self):
        """expire_on_commit=True & committing computer and code objects with
        their built-in store function."""

        self.set_connection(expire_on_commit=True)
        session = aiida.backends.sqlalchemy.get_scoped_session()

        email = get_manager().get_profile().default_user
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        computer = self.backend.computers.create(
            label='localhost', hostname='localhost', transport_type='core.local', scheduler_type='core.pbspro'
        )
        computer.store()

        self.backend.nodes.create(node_type='', user=user).store()
        self.drop_connection()

    def test_session_update_and_expiration_3(self):
        """
        expire_on_commit=False & adding manually and committing
        computer and code objects.
        """
        self.set_connection(expire_on_commit=False)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        email = get_manager().get_profile().default_user
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(
            label='localhost', hostname='localhost', transport_type='core.local', scheduler_type='core.pbspro'
        )
        computer = self.backend.computers.create(**defaults)
        session.add(computer.dbmodel)
        session.commit()

        node = self.backend.nodes.create(node_type='', user=user).store()
        session.add(node.dbmodel)
        session.commit()

        self.drop_connection()

    def test_session_update_and_expiration_4(self):
        """expire_on_commit=False & committing computer and code objects with
        their built-in store function."""

        self.set_connection(expire_on_commit=False)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        email = get_manager().get_profile().default_user
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(
            label='localhost', hostname='localhost', transport_type='core.local', scheduler_type='core.pbspro'
        )
        computer = self.backend.computers.create(**defaults)
        computer.store()

        self.backend.nodes.create(node_type='', user=user).store()
        self.drop_connection()

    def test_node_access_with_sessions(self):
        """This checks that changes to a node from a different session (e.g. different interpreter,
        or the daemon) are immediately reflected on the AiiDA node when read directly e.g. a change
        to node.description will immediately be seen.

        Tests for bug #1372"""
        import aiida.backends.sqlalchemy as sa
        from aiida.common import timezone

        session = sessionmaker(bind=sa.ENGINE, future=True)
        custom_session = session()

        try:
            user = self.backend.users.create(email='test@localhost').store()
            node = self.backend.nodes.create(node_type='', user=user).store()
            master_session = node.dbmodel.session
            assert master_session is not custom_session

            # Manually load the DbNode in a different session
            dbnode_reloaded = custom_session.get(sa.models.node.DbNode, node.id)

            # Now, go through one by one changing the possible attributes (of the model)
            # and check that they're updated when the user reads them from the aiida node

            for str_attr in ['label', 'description']:
                do_value_checks(custom_session, node, dbnode_reloaded, str_attr, 'original', 'changed')

            for str_attr in ['ctime', 'mtime']:
                do_value_checks(custom_session, node, dbnode_reloaded, str_attr, timezone.now(), timezone.now())

            # Attributes
            assert node.attributes == dbnode_reloaded.attributes
            dbnode_reloaded.attributes['test_attrs'] = 'Boo!'
            custom_session.commit()
            assert node.attributes == dbnode_reloaded.attributes

            # Extras
            assert node.extras == dbnode_reloaded.extras
            dbnode_reloaded.extras['test_extras'] = 'Boo!'
            custom_session.commit()
            assert node.attributes == dbnode_reloaded.attributes
        finally:
            custom_session.close()


def check_attrs_match(name, dbnode_original, dbnode_reloaded):
    original_attr = getattr(dbnode_original, name)
    reloaded_attr = getattr(dbnode_reloaded, name)
    assert original_attr == reloaded_attr, f"Values of '{name}' don't match ({original_attr} != {reloaded_attr})"


def do_value_checks(session, dbnode_original, dbnode_reloaded, attr_name, original, changed):
    """Run the value check"""
    try:
        setattr(dbnode_original, attr_name, original)
    except AttributeError:
        # This may mean that it is immutable, but we should still be able to
        # change it below directly through the dbnode
        pass
    # Refresh the custom session and make sure they match
    session.refresh(dbnode_reloaded, attribute_names=[attr_name])
    check_attrs_match(attr_name, dbnode_original, dbnode_reloaded)

    # Change the value in the custom session via the DbNode
    setattr(dbnode_reloaded, attr_name, changed)
    session.commit()

    # Check that the Node 'sees' the change
    check_attrs_match(attr_name, dbnode_original, dbnode_reloaded)
