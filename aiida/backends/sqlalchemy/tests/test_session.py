# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Testing Session possible problems.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from sqlalchemy.orm import sessionmaker

import aiida.backends
from aiida.backends.testbase import AiidaTestCase
from aiida.manage.manager import get_manager


class TestSessionSqla(AiidaTestCase):
    """
    The following tests check that the session works as expected in some
    problematic examples. When a session is initialized with
    expire_on_commit=False allows more permissive behaviour since committed
    objects that remain in the session do not need refresh. The opposite
    happens when expire_on_commit=True.

    Moreover, 2 ways of storing objects are tested, i.e. adding the objects
    manually to the session and committing it & by using the build-in store
    method of the ORM objects.
    """

    def set_connection(self, expire_on_commit=True):
        # Creating a sessionmaker with the desired parameters
        # Note: to check if this is still correct with the new
        # way of managing connections and sessions in SQLA...
        # For instance, we should use probably a scopedsession wrapper
        Session = sessionmaker(expire_on_commit=expire_on_commit)
        aiida.backends.sqlalchemy.sessionfactory = Session(
            bind=self._AiidaTestCase__backend_instance.connection)

        # Cleaning the database
        self.clean_db()
        aiida.backends.sqlalchemy.get_scoped_session().expunge_all()

    def drop_connection(self):
        session = aiida.backends.sqlalchemy.get_scoped_session()
        session.expunge_all()
        session.close()
        aiida.backends.sqlalchemy.sessionfactory = None

    def test_session_update_and_expiration_1(self):
        """
        expire_on_commit=True & adding manually and committing
        computer and code objects.
        """
        self.set_connection(expire_on_commit=True)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        email = get_manager().get_profile().default_user_email
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro')
        computer = self.backend.computers.create(**defaults)
        session.add(computer.dbmodel)
        session.commit()

        node = self.backend.nodes.create(node_type='', user=user).store()
        session.add(node.dbmodel)
        session.commit()

        self.drop_connection()

    def test_session_update_and_expiration_2(self):
        """
        expire_on_commit=True & committing computer and code objects with
        their built-in store function.
        """
        session = aiida.backends.sqlalchemy.get_scoped_session()

        self.set_connection(expire_on_commit=True)

        email = get_manager().get_profile().default_user_email
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro')
        computer = self.backend.computers.create(**defaults)
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

        email = get_manager().get_profile().default_user_email
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro')
        computer = self.backend.computers.create(**defaults)
        session.add(computer.dbmodel)
        session.commit()

        node = self.backend.nodes.create(node_type='', user=user).store()
        session.add(node.dbmodel)
        session.commit()

        self.drop_connection()

    def test_session_update_and_expiration_4(self):
        """
        expire_on_commit=False & committing computer and code objects with
        their built-in store function.
        """
        self.set_connection(expire_on_commit=False)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        email = get_manager().get_profile().default_user_email
        user = self.backend.users.create(email=email)
        session.add(user.dbmodel)
        session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro')
        computer = self.backend.computers.create(**defaults)
        computer.store()

        self.backend.nodes.create(node_type='', user=user).store()
        self.drop_connection()

    def test_node_access_with_sessions(self):
        """
        This checks that changes to a node from a different session (e.g. different interpreter,
        or the daemon) are immediately reflected on the AiiDA node when read directly e.g. a change
        to node.description will immediately be seen.

        Tests for bug #1372
        """
        from aiida.common import timezone
        import aiida.backends.sqlalchemy as sa
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=sa.engine)
        custom_session = Session()

        user = self.backend.users.create(email='test@localhost').store()
        node = self.backend.nodes.create(node_type='', user=user).store()
        master_session = node.dbmodel.session
        self.assertIsNot(master_session, custom_session)

        # Manually load the DbNode in a different session
        dbnode_reloaded = custom_session.query(sa.models.node.DbNode).get(node.id)

        # Now, go through one by one changing the possible attributes (of the model)
        # and check that they're updated when the user reads them from the aiida node

        def check_attrs_match(name):
            node_attr = getattr(node, name)
            dbnode_attr = getattr(dbnode_reloaded, name)
            self.assertEqual(
                node_attr, dbnode_attr,
                "Values of '{}' don't match ({} != {})".format(name, node_attr, dbnode_attr))

        def do_value_checks(attr_name, original, changed):
            try:
                setattr(node, attr_name, original)
            except AttributeError:
                # This may mean that it is immutable, but we should still be able to
                # change it below directly through the dbnode
                pass
            # Refresh the custom session and make sure they match
            custom_session.refresh(dbnode_reloaded, attribute_names=[str_attr])
            check_attrs_match(attr_name)

            # Change the value in the custom session via the DbNode
            setattr(dbnode_reloaded, attr_name, changed)
            custom_session.commit()

            # Check that the Node 'sees' the change
            check_attrs_match(str_attr)

        for str_attr in ['label', 'description']:
            do_value_checks(str_attr, 'original', 'changed')

        # Since we already changed an attribute twice, the starting nodeversion is 3 and not 1
        do_value_checks('nodeversion', 3, 4)
        do_value_checks('public', True, False)

        for str_attr in ['ctime', 'mtime']:
            do_value_checks(str_attr, timezone.now(), timezone.now())

        # Attributes
        self.assertDictEqual(node.attributes, dbnode_reloaded.attributes)
        dbnode_reloaded.attributes['test_attrs'] = 'Boo!'
        custom_session.commit()
        self.assertDictEqual(node.attributes, dbnode_reloaded.attributes)

        # Extras
        self.assertDictEqual(node.extras, dbnode_reloaded.extras)
        dbnode_reloaded.extras['test_extras'] = 'Boo!'
        custom_session.commit()
        self.assertDictEqual(node.attributes, dbnode_reloaded.attributes)
