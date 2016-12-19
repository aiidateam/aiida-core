# -*- coding: utf-8 -*-
"""
Testing Session possible problems.
"""

import os

from sqlalchemy.orm import sessionmaker

import aiida.backends
from aiida.backends.testbase import AiidaTestCase
from aiida.common.utils import get_configured_user_email

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


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
        Session = sessionmaker(expire_on_commit=expire_on_commit)
        aiida.backends.sqlalchemy.session = Session(
            bind=self._AiidaTestCase__backend_instance.connection)

        # Cleaning the database
        self.clean_db()
        aiida.backends.sqlalchemy.session.expunge_all()

    def drop_connection(self):
        aiida.backends.sqlalchemy.session.expunge_all()
        aiida.backends.sqlalchemy.session.close()
        aiida.backends.sqlalchemy.session = None

    def test_session_update_and_expiration_1(self):
        """
        expire_on_commit=True & adding manually and committing
        computer and code objects.
        """
        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        self.set_connection(expire_on_commit=True)

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        aiida.backends.sqlalchemy.session.add(computer._dbcomputer)
        aiida.backends.sqlalchemy.session.commit()

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        aiida.backends.sqlalchemy.session.add(code.dbnode)
        aiida.backends.sqlalchemy.session.commit()

        self.drop_connection()

    def test_session_update_and_expiration_2(self):
        """
        expire_on_commit=True & committing computer and code objects with
        their built-in store function.
        """
        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        self.set_connection(expire_on_commit=True)

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        computer.store()

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        code.store()

        self.drop_connection()

    def test_session_update_and_expiration_3(self):
        """
        expire_on_commit=False & adding manually and committing
        computer and code objects.
        """
        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        self.set_connection(expire_on_commit=False)

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        aiida.backends.sqlalchemy.session.add(computer._dbcomputer)
        aiida.backends.sqlalchemy.session.commit()

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        aiida.backends.sqlalchemy.session.add(code.dbnode)
        aiida.backends.sqlalchemy.session.commit()

        self.drop_connection()

    def test_session_update_and_expiration_4(self):
        """
        expire_on_commit=False & committing computer and code objects with
        their built-in store function.
        """
        self.set_connection(expire_on_commit=False)

        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        user = User(email=get_configured_user_email())
        aiida.backends.sqlalchemy.session.add(user._dbuser)
        aiida.backends.sqlalchemy.session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        computer.store()

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        code.store()

        self.drop_connection()
