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
Base class for AiiDA tests
"""
from django.utils import unittest
import shutil
import os
from aiida.backends.testimplbase import AiidaTestImplementation

# Add a new entry here if you add a file with tests under aiida.backends.djsite.db.subtests
# The key is the name to use in the 'verdi test' command (e.g., a key 'generic'
# can be run using 'verdi test db.generic')
# The value must be the module name containing the subclasses of unittest.TestCase


# This contains the codebase for the setUpClass and tearDown methods used internally by the AiidaTestCase
# This inherits only from 'object' to avoid that it is picked up by the automatic discovery of tests
# (It shouldn't, as it risks to destroy the DB if there are not the checks in place, and these are
# implemented in the AiidaTestCase
class DjangoTests(AiidaTestImplementation):
    """
    Automatically takes care of the setUpClass and TearDownClass, when needed.
    """

    # Note this is has to be a normal method, not a class method
    def setUpClass_method(self):
        self.clean_db()
        self.insert_data()

    def setUp_method(self):
        pass

    def tearDown_method(self):
        pass

    def insert_data(self):
        """
        Insert default data into the DB.
        """
        from django.core.exceptions import ObjectDoesNotExist

        from aiida.backends.djsite.db.models import DbUser
        from aiida.orm.computer import Computer
        from aiida.common.utils import get_configured_user_email
        # We create the user only once:
        # Otherwise, get_automatic_user() will fail when the
        # user is recreated because it caches the user!
        # In any case, store it in self.user though
        try:
            self.user = DbUser.objects.get(email=get_configured_user_email())
        except ObjectDoesNotExist:
            self.user = DbUser.objects.create_user(get_configured_user_email(),
                                                   'fakepwd')
        # Reqired by the calling class
        self.user_email = self.user.email

        # Also self.computer is required by the calling class
        self.computer = Computer(name='localhost',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='pbspro',
                                workdir='/tmp/aiida')
        self.computer.store()

    def clean_db(self):
        from aiida.backends.djsite.db.models import (
            DbComputer, DbUser, DbWorkflow, DbWorkflowStep, DbWorkflowData)
        from aiida.common.utils import get_configured_user_email

        # Complicated way to make sure we 'unwind' all the relationships
        # between workflows and their children.
        DbWorkflowStep.calculations.through.objects.all().delete()
        DbWorkflowStep.sub_workflows.through.objects.all().delete()
        DbWorkflowData.objects.all().delete()
        DbWorkflowStep.objects.all().delete()
        DbWorkflow.objects.all().delete()

        # Delete groups
        from aiida.backends.djsite.db.models import DbGroup

        DbGroup.objects.all().delete()

        # I first need to delete the links, because in principle I could
        # not delete input nodes, only outputs. For simplicity, since
        # I am deleting everything, I delete the links first
        from aiida.backends.djsite.db.models import DbLink

        DbLink.objects.all().delete()

        # Then I delete the nodes, otherwise I cannot
        # delete computers and users
        from aiida.backends.djsite.db.models import DbNode

        DbNode.objects.all().delete()

        # I delete all the users except the default user.
        # See discussion in setUpClass
        DbUser.objects.exclude(email=get_configured_user_email()).delete()

        DbComputer.objects.all().delete()

        from aiida.backends.djsite.db.models import DbLog

        DbLog.objects.all().delete()

    # Note this is has to be a normal method, not a class method
    def tearDownClass_method(self):
        from aiida.settings import REPOSITORY_PATH
        from aiida.common.setup import TEST_KEYWORD
        from aiida.common.exceptions import InvalidOperation

        base_repo_path = os.path.basename(
            os.path.normpath(REPOSITORY_PATH))
        if TEST_KEYWORD not in base_repo_path:
            raise InvalidOperation("Be careful. The repository for the tests "
                                   "is not a test repository. I will not "
                                   "empty the database and I will not delete "
                                   "the repository. Repository path: "
                                   "{}".format(REPOSITORY_PATH))

        self.clean_db()

        # I clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)
