"""
Base class for AiiDA tests
"""
from django.utils import unittest

# Add a new entry here if you add a file with tests under aiida.djsite.db.subtests
# The key is the name to use in the 'verdi test' command (e.g., a key 'generic'
# can be run using 'verdi test db.generic')
# The value must be the module name containing the subclasses of unittest.TestCase
db_test_list = {
    'generic': 'aiida.djsite.db.subtests.generic',
    'qepw': 'aiida.djsite.db.subtests.quantumespressopw'}

class AiidaTestCase(unittest.TestCase):
    """
    Automatically takes care of the setUpClass and TearDownClass, when needed.
    """
    @classmethod
    def setUpClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from aiida.orm import Computer

        cls.user = User.objects.create_user(getpass.getuser(),
                                            'unknown@mail.com', 'fakepwd')
        cls.computer = Computer(name='localhost',
                                hostname='localhost',
                                transport_type='ssh',
                                scheduler_type='pbspro',
                                workdir='/tmp/aiida')
        cls.computer.store()

    @classmethod
    def tearDownClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from django.core.exceptions import ObjectDoesNotExist
        from aiida.djsite.db.models import DbComputer

        # I first delete the workflows
        from aiida.djsite.db.models import DbWorkflow
        DbWorkflow.objects.filter().delete()

        # I first need to delete the links, because in principle I could
        # not delete input nodes, only outputs. For simplicity, since
        # I am deleting everything, I delete the links first
        from aiida.djsite.db.models import DbLink
        DbLink.objects.filter().delete()
        
        # Then I delete the nodes, otherwise I cannot
        # delete computers and users
        from aiida.djsite.db.models import DbNode
        DbNode.objects.filter().delete()

        try:
            User.objects.get(username=getpass.getuser).delete()
        except ObjectDoesNotExist:
            pass
        
        DbComputer.objects.filter().delete()
