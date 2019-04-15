# -*- coding: utf-8 -*-
"""
Base class for AiiDA tests
"""
from django.utils import unittest
import shutil
import tempfile
import os

# Add a new entry here if you add a file with tests under aiida.backends.djsite.db.subtests
# The key is the name to use in the 'verdi test' command (e.g., a key 'generic'
# can be run using 'verdi test db.generic')
# The value must be the module name containing the subclasses of unittest.TestCase

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."

db_test_list = {
    'generic': ['aiida.backends.djsite.db.subtests.generic'],
    'nodes': ['aiida.backends.djsite.db.subtests.nodes'],
    'nwchem': ['aiida.backends.djsite.db.subtests.nwchem'],
    'dataclasses': ['aiida.backends.djsite.db.subtests.dataclasses'],
    'qepw': ['aiida.backends.djsite.db.subtests.quantumespressopw'],
    'codtools': ['aiida.backends.djsite.db.subtests.codtools'],
    'dbimporters': ['aiida.backends.djsite.db.subtests.dbimporters'],
    'export_and_import': ['aiida.backends.djsite.db.subtests.export_and_import'],
    'migrations': ['aiida.backends.djsite.db.subtests.migrations'],
    'parsers': ['aiida.backends.djsite.db.subtests.parsers'],
    'qepwinputparser': ['aiida.backends.djsite.db.subtests.pwinputparser'],
    'qepwimmigrant': ['aiida.backends.djsite.db.subtests.quantumespressopwimmigrant'],
    'tcodexporter': ['aiida.backends.djsite.db.subtests.tcodexporter'],
    'workflows': ['aiida.backends.djsite.db.subtests.workflows'],
    'query': ['aiida.backends.djsite.db.subtests.query'],
    'backup': ['aiida.backends.djsite.db.subtests.backup_script',
               'aiida.backends.djsite.db.subtests.backup_setup_script'],
}


class AiidaTestCase(unittest.TestCase):
    """
    Automatically takes care of the setUpClass and TearDownClass, when needed.
    """

    @classmethod
    def setUpClass(cls):

        from django.core.exceptions import ObjectDoesNotExist

        from aiida.backends.djsite.db.models import DbUser
        from aiida.orm.computer import Computer
        from aiida.common.utils import get_configured_user_email
        # I create the user only once:

        # We create the user only once:
        # Otherwise, get_automatic_user() will fail when the
        # user is recreated because it caches the user!
        # In any case, store it in cls.user though
        # Other possibility: flush the user cache on delete
        try:
            cls.user = DbUser.objects.get(email=get_configured_user_email())
        except ObjectDoesNotExist:
            cls.user = DbUser.objects.create_user(get_configured_user_email(),
                                                  'fakepwd')
        cls.computer = Computer(name='localhost',
                                hostname='localhost',
                                transport_type='local',
                                scheduler_type='pbspro',
                                workdir='/tmp/aiida')
        cls.computer.store()

    @classmethod
    def tearDownClass(cls):
        from aiida.settings import REPOSITORY_PATH
        from aiida.common.setup import TEMP_TEST_REPO_PREFIX
        from aiida.common.exceptions import InvalidOperation
        if not REPOSITORY_PATH.startswith(
                os.path.join("/", tempfile.gettempprefix(),
                             TEMP_TEST_REPO_PREFIX)):
            raise InvalidOperation("Be careful. The repository for the tests "
                                   "is not a test repository. I will not "
                                   "empty the database and I will not delete "
                                   "the repository. Repository path: "
                                   "{}".format(REPOSITORY_PATH))

        from aiida.backends.djsite.db.models import DbComputer

        # I first delete the workflows
        from aiida.backends.djsite.db.models import DbWorkflow

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

        ## I do not delete it, see discussion in setUpClass
        # try:
        #    DbUser.objects.get(email=get_configured_user_email()).delete()
        # except ObjectDoesNotExist:
        #    pass

        DbComputer.objects.all().delete()

        from aiida.backends.djsite.db.models import DbLog

        DbLog.objects.all().delete()

        # I clean the test repository
        shutil.rmtree(REPOSITORY_PATH, ignore_errors=True)
        os.makedirs(REPOSITORY_PATH)
