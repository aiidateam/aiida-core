"""
This file contains tests for AIDA.
They are executed when when you run "manage.py test" or
"manage.py test aidadb" (much faster)

"""
from django.utils import unittest
from aidadb.models import CalcStatus, CalcType, Code, CodeStatus
from aidadb.models import CodeType, Computer, Project, Calc
from django.contrib.auth.models import User as AuthUser
import getpass
from django.db import IntegrityError

from django.core import management

class SimpleTest(unittest.TestCase):
    # List here fixtures to be load
    # for some reasons it doesn't work... for the moment I just load it in
    # setUp, even if possibly redundant
    #fixtures = ['testcalcstatus']

    def setUp(self):
        AuthUser.objects.get_or_create(username=getpass.getuser())
        # To be loaded in the correct order!
        management.call_command('loaddata', 'testproject', verbosity=0)
        management.call_command('loaddata', 'testcomputer', verbosity=0)
        management.call_command('loaddata', 'testcalcstatus', verbosity=0)
        management.call_command('loaddata', 'testcalctype', verbosity=0)
        management.call_command('loaddata', 'testcodestatus', verbosity=0)
        management.call_command('loaddata', 'testcodetype', verbosity=0)
        management.call_command('loaddata', 'testcode', verbosity=0)

        # I insert a new calculation
        code = Code.objects.get(title__istartswith="pw.x")
        computer = code.computer
        project = Project.objects.get(title__istartswith="test")
        initial_status = CalcStatus.objects.get(title="Submitting")
        calc_type = CalcType.objects.get(title="DFT SCF")
        self.the_calc = Calc.objects.create(title="test calculation",computer=computer,
                            code=code,project=project,
                            status=initial_status,
                            type=calc_type)

    def test_submission(self):
        """
        Tests that I can submit a calculation.
        """
        self.the_calc.submit()

    def tearDown(self):
        """
        Important. If I have more than one test_ function within this class,
        the setUp() function will be called more than once. This will give
        problems since the calculation is created more than once.
        """
        self.the_calc.delete()

# Note: tests must start with 'test_'
#    def test_failing_test(self):
#        """
#        Failing test to debug the testing suite.
#        """
#        self.assertEqual(1 + 1, 3)
