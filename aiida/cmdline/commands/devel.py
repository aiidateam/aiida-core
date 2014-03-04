import sys
import os

import aiida
from aiida.cmdline.baseclass import VerdiCommand
from aiida.common.utils import load_django
from aiida.cmdline import pass_to_django_manage, execname

class Devel(VerdiCommand):
    """
    AiiDA commands for developers

    Provides a set of tools for developers. For instance, it allows to run
    the django tests for the db application and the unittests of
    the AiiDA modules.
    
    If you want to limit the tests to a specific subset of modules,
    pass them as parameters. 
    
    An invalid parameter will make the code print the list of all
    valid parameters.
    
    Note: the test called 'db' will run all db.* tests.
    """
    base_allowed_test_folders = [
        'aiida.scheduler', 
        'aiida.transport',
        'aiida.common',
        ]
    
    _dbrawprefix = "db"
    _dbprefix = _dbrawprefix + "."

    def __init__(self,*args,**kwargs):
        from aiida.djsite.db.testbase import db_test_list
        
        super(Devel, self).__init__(*args, **kwargs)

        self.valid_subcommands = {
            'tests': (self.run_tests, self.complete_tests),
            }
        
        # The content of the dict is:
        #   None for a simple folder test
        #   a list of strings for db tests, one for each test to run
        self.allowed_test_folders = {}
        for k in self.base_allowed_test_folders:
            self.allowed_test_folders[k] = None
        for dbtest in db_test_list:
            self.allowed_test_folders["{}{}".format(self._dbprefix, dbtest)] = [dbtest]
        self.allowed_test_folders[self._dbrawprefix] = db_test_list
    
    def run(self,*args):       
        try:
            function_to_call = self.valid_subcommands[args[0]][0]
        except IndexError:
            function_to_call = self.no_subcommand
        except KeyError:
            function_to_call = self.invalid_subcommand
            
        function_to_call(*args[1:])
    
    def complete(self,subargs_idx, subargs):
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        elif subargs_idx >= 1:
            try:
                first_subarg = subargs[0]
            except  IndexError:
                first_subarg = ''
            try:
                complete_function = self.valid_subcommands[first_subarg][1] 
            except KeyError:
                # No completion
                print ""
                return
            print complete_function(subargs_idx - 1, subargs[1:])

    def no_subcommand(self,*args):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'devel'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'devel'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)
        
    def run_tests(self,*args):
        import unittest
        import tempfile
        from aiida.djsite.settings import settings

        db_test_list = []
        test_folders = []
        do_db = False
        if args:
            for arg in args:
                if arg in self.allowed_test_folders:
                    dbtests = self.allowed_test_folders[arg]
                    # Anything that has been added is a DB test                    
                    if dbtests is not None:
                        do_db = True
                        for dbtest in dbtests:
                            db_test_list.append(dbtest)
                    else:
                        test_folders.append(arg)
                else:
                    print >> sys.stderr, (
                        "{} is not a valid test. "
                        "Allowed test folders are:".format(arg))
                    print >> sys.stderr, "\n".join(
                        '  * {}'.format(a) for a in sorted(
                            self.allowed_test_folders.keys()))
                    sys.exit(1)
        else:
            # Without arguments, run all tests
            do_db = True
            for k, v in self.allowed_test_folders.iteritems():
                if v is None:
                    # Non-db tests
                    test_folders.append(k)
                else:
                    # DB test
                    for dbtest in v:
                        db_test_list.append(dbtest)                    

        for test_folder in test_folders:
            print "v"*75
            print ">>> Tests for module {} <<<".format(test_folder.ljust(50))
            print "^"*75
            testsuite = unittest.defaultTestLoader.discover(
                test_folder,top_level_dir = os.path.dirname(aiida.__file__))
            test_runner = unittest.TextTestRunner()
            test_runner.run( testsuite )

        if do_db:
            # As a first thing, I want to set the correct flags.
            # This allow to work on temporary DBs and a temporary repository.

            ## Setup a sqlite3 DB for tests (WAY faster, since it remains in-memory
            ## and not on disk.
            # if you define such a variable to False, it will use the same backend
            # that you have already configured also for tests. Otherwise, 
            # Setup a sqlite3 DB for tests (WAY faster, since it remains in-memory)

            # TODO: allow the use of this flag
            #if confs.get('use_inmemory_sqlite_for_tests', True):
            settings.DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}
            ###################################################################
            # IMPORTANT! Choose a different repository location, otherwise 
            # real data will be destroyed during tests!!
            # The location is automatically created with the tempfile module
            # Typically, under linux this is created under /tmp
            # and is not deleted at the end of the run.
            settings.LOCAL_REPOSITORY = tempfile.mkdtemp(prefix='aiida_repository_')
            # I write the local repository on stderr, so that the user running
            # the tests knows where the files are being stored
            print >> sys.stderr, "########################################"
            print >> sys.stderr,  "# LOCAL AiiDA REPOSITORY FOR TESTS:"
            print >> sys.stderr, "# {}".format(settings.LOCAL_REPOSITORY)
            print >> sys.stderr, "########################################"
            # Here. I set the correct signal to attach to when we want to
            # perform an operation after all tables are created (e.g., creation
            # of the triggers).
            # By default, in djsite/settings/settings.py this is south->post_migrate,
            # here we set it to django->post_syncdb because we have set
            # SOUTH_TESTS_MIGRATE = False
            # in the settings.
            settings.AFTER_DATABASE_CREATION_SIGNAL = 'post_syncdb'
            
            
            ##################################################################
            ## Only now I set the aiida_test_list variable so that tests can run
            settings.aiida_test_list = db_test_list
            
            print "v"*75
            print (">>> Tests for django db application   "
                   "                                  <<<")
            print "^"*75            
            pass_to_django_manage([execname, 'test', 'db'])

    def complete_tests(self, subargs_idx, subargs):
        """
        I complete with subargs that were not used yet.
        """
        # I remove the one on which I am, so if I wrote all of it but
        # did not press space, it will get completed
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx+1:]
        # I create a list of the tests that are not already written on the 
        # command line
        remaining_tests = (
            set(self.allowed_test_folders) - set(other_subargs))

        return " ".join(sorted(remaining_tests))

