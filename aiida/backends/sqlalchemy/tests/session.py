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

import os

from sqlalchemy.orm import sessionmaker

import aiida.backends
from aiida.backends.testbase import AiidaTestCase
from aiida.common.utils import get_configured_user_email



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
        ## Note: to check if this is still correct with the new
        ## way of managing connections and sessions in SQLA...
        ## For instance, we should use probably a scopedsession wrapper
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
        from aiida.orm.computer import Computer
        from aiida.orm.code import Code
        from aiida.orm.user import User

        self.set_connection(expire_on_commit=True)

        session = aiida.backends.sqlalchemy.get_scoped_session()

        user = User(email=get_configured_user_email())
        session.add(user._dbuser)
        session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        session.add(computer._dbcomputer)
        session.commit()

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        session.add(code.dbnode)
        session.commit()

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

        session = aiida.backends.sqlalchemy.get_scoped_session()

        self.set_connection(expire_on_commit=True)

        user = User(email=get_configured_user_email())
        session.add(user._dbuser)
        session.commit()

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

        session = aiida.backends.sqlalchemy.get_scoped_session()

        user = User(email=get_configured_user_email())
        session.add(user._dbuser)
        session.commit()

        defaults = dict(name='localhost',
                        hostname='localhost',
                        transport_type='local',
                        scheduler_type='pbspro',
                        workdir='/tmp/aiida')
        computer = Computer(**defaults)
        session.add(computer._dbcomputer)
        session.commit()

        code = Code()
        code.set_remote_computer_exec((computer, '/x.x'))
        session.add(code.dbnode)
        session.commit()

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

        session = aiida.backends.sqlalchemy.get_scoped_session()

        user = User(email=get_configured_user_email())
        session.add(user._dbuser)
        session.commit()

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
