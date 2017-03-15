# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import unittest
import tempfile
import os.path
import shutil

from aiida.common.exceptions import NotExistent



class DbTestCase(unittest.TestCase):
    """
    Automatically takes care of the setUpClass and TearDownClass, when needed.

    This class can be used by any unit test that requires database interaction.
    """

    @classmethod
    def setUpClass(cls):
        from aiida.orm.user import User
        from aiida.orm.computer import Computer
        from aiida.common.utils import get_configured_user_email
        # I create the user only once:

        # We create the user only once:
        # Otherwise, get_automatic_user() will fail when the
        # user is recreated because it caches the user!
        # In any case, store it in cls.user though
        # Other possibility: flush the user cache on delete
        users = User.search_for_users(email=get_configured_user_email())
        assert(len(users) <= 1)
        if users:
            cls.user = users[0]
        else:
            cls.user = User(get_configured_user_email())
            cls.user.password = 'fakepwd'
            cls.user.save()

        try:
            cls.computer = Computer.get('test_comp')
        except NotExistent:
            cls.computer = Computer(name='test_comp',
                                    hostname='localhost',
                                    transport_type='local',
                                    scheduler_type='pbspro',
                                    workdir='/tmp/aiida')
            cls.computer.store()

    @classmethod
    def tearDownClass(cls):
        # from aiida.settings import REPOSITORY_PATH
        # from aiida.common.setup import TEMP_TEST_REPO_PREFIX
        # from aiida.common.exceptions import InvalidOperation
        # if not REPOSITORY_PATH.startswith(
        #         os.path.join("/", tempfile.gettempprefix(),
        #                      TEMP_TEST_REPO_PREFIX)):
        #     raise InvalidOperation("Be careful. The repository for the tests "
        #                            "is not a test repository. I will not "
        #                            "empty the database and I will not delete "
        #                            "the repository. Repository path: "
        #                            "{}".format(REPOSITORY_PATH))

        # from aiida.backends.djsite.db.models import DbComputer

        # I first delete the workflows
        # from aiida.backends.djsite.db.models import DbWorkflow

        # DbWorkflow.objects.all().delete()

        # Delete groups
        # from aiida.backends.djsite.db.models import DbGroup

        # DbGroup.objects.all().delete()

        # I first need to delete the links, because in principle I could
        # not delete input nodes, only outputs. For simplicity, since
        # I am deleting everything, I delete the links first
        # from aiida.backends.djsite.db.models import DbLink

        # DbLink.objects.all().delete()

        # Then I delete the nodes, otherwise I cannot
        # delete computers and users
        from aiida.backends.djsite.db.models import DbNode

        # DbNode.objects.all().delete()

        ## I do not delete it, see discussion in setUpClass
        # try:
        #    DbUser.objects.get(email=get_configured_user_email()).delete()
        # except ObjectDoesNotExist:
        #    pass

        import aiida.orm.computer as computer
        try:
            computer.Util.get_default().delete_computer(cls.computer.pk)
        except:
            pass

        # from aiida.backends.djsite.db.models import DbLog

        # DbLog.objects.all().delete()

        # I clean the test repository
        # shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        # os.makedirs(REPOSITORY_PATH)
