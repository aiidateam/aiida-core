"""
Command line commands for the main executable 'verdi' of aiida

If you want to define a new command line parameter, just define a new
class inheriting from VerdiCommand, and define a run(self,*args) method
accepting a variable-length number of parameters args
(the command-line parameters), which will be invoked when
this executable is called as
verdi NAME

Don't forget to add the docstring to the class: the first line will be the
short description, the following ones the long description.

NOTE! Commands that run tests should ALWAYS contain the string 'test'.
NOTE! Command that do NOT run tests must NOT contain the string 'test'.
(This is due to how it is implemented the logic on tests in settings.py)

## TODO: implement bash completion
"""
import sys
import os
import getpass

import aida
from aida.common.exceptions import ConfigurationError
from aida.cmdline.baseclass import VerdiCommand

## Import here from other files
from aida.cmdline.commands.daemon import Daemon

# default execname; can be substituted later in the call from
# exec_from_cmdline
execname = 'verdi'

########################################################################
# HERE STARTS THE COMMAND FUNCTION LIST
########################################################################

class CompletionCommand(VerdiCommand):
    """
    Return the bash completion function to put in ~/.bashrc.

    This command prints on screen the function to be inserted in 
    your .bashrc command. You can copy and paste the output, or simply
    add 
    eval `verdi completioncommand`
    to your .bashrc, *AFTER* having added the aiida/bin directory to the path.
    """
    def run(self, *args):
        """
        I put the documentation here, and I don't print it, so we
        don't clutter too much the .bashrc.

        * "${THE_WORDS[@]}" (with the @) puts each element as a different
          parameter; note that the variable expansion etc. is performed

        * I add a 'x' at the end and then remove it; in this way, $( ) will
          not remove trailing spaces

        * If the completion command did not print anything, we use
          the default bash completion for filenames
          
        * If instead the code prints something empty, thanks to the workaround
          above $OUTPUT is not empty, so we do go the the 'else' case
          and then, no substitution is suggested.
        """

        print """
function _aiida_verdi_completion
{
    OUTPUT=$( $1 completion "$COMP_CWORD" "${COMP_WORDS[@]}" ; echo 'x')
    OUTPUT=${OUTPUT%x}
    if [ -z "$OUTPUT" ]
    then
        COMPREPLY=( $(compgen -o default -- "${COMP_WORDS[COMP_CWORD]}" ) )
    else
        COMPREPLY=( $(compgen -W "$OUTPUT" -- "${COMP_WORDS[COMP_CWORD]}" ) )
    fi
}
complete -F _aiida_verdi_completion verdi
"""

    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""


class Completion(VerdiCommand):
    """
    Manages bash completion. 

    Return a list of available commands, separated by spaces.
    Calls the correct function of the command if the TAB has been
    pressed after the first command.

    Returning without printing will use the default bash completion.
    """
    # TODO: manage completion at a deeper level

    def run(self,*args):
        try:
            cword = int(args[0])
            if cword <= 0:
                cword = 1
        except IndexError:
            cword = 1
        except ValueError:
            return

        if cword == 1:
            print " ".join(sorted(short_doc.keys()))
            return
        else:
            try:
                # args[0] is cword;
                # args[1] is the executable (verdi)
                # args[2] is the command for verdi
                # args[3:] are the following subargs
                command = args[2]
            except IndexError:
                return
            try:
                CommandClass = list_commands[command]
            except KeyError:
                return
            CommandClass().complete(subargs_idx=cword-2, subargs=args[3:])

class ListParams(VerdiCommand):
    """
    List available commands.

    List available commands and their short description.
    For the long description, use the 'help' command.
    """
    
    def run(self,*args):
        print get_listparams()

class Help(VerdiCommand):
    """
    Describe a specific command.

    Pass a further argument to get a description of a given command.
    """
    
    def run(self, *args):
        try:
            command = args[0]
        except IndexError:
            print get_listparams()
            print ""
            print ("Use '{} help <command>' for more information "
                   "on a specific command.".format(execname))
            sys.exit(1)
    
        if command in short_doc:
            print "Description for '%s %s'" % (execname, command)
            print ""
            print "**", short_doc[command]
            if command in long_doc:
                print long_doc[command]
        else:
            print >> sys.stderr, (
                "{}: '{}' is not a valid command. "
                "See '{} help' for more help.".format(
                    execname, command, execname))
            get_command_suggestion(command)
            sys.exit(1)

    def complete(self, subargs_idx, subargs):
        if subargs_idx == 0:
            print " ".join(sorted(short_doc.keys()))
        else:
            print ""
    
class SyncDB(VerdiCommand):
    """
    Create new tables in the database.

    This command calls the Django 'manage.py syncdb' command to create
    new tables in the database, and possibly install triggers.
    Pass a --migrate option to automatically also migrate the tables
    managed using South migrations.
    """

    def run(self,*args):
        pass_to_django_manage([execname, 'syncdb'] + list(args))

class Migrate(VerdiCommand):
    """
    Migrate tables and data using django-south.
    
    This command calls the Django 'manage.py migrate' command to migrate
    tables managed by django-south to their most recent version.
    """
    def run(self,*args):
        pass_to_django_manage([execname, 'migrate'] + list(args))

class DjangoTest(VerdiCommand):
    """
    Runs the django tests.

    This command calls the Django 'manage.py test' command to run the
    unittests of django. Pass the name of an application to restrict
    the tests to those of the specific application.
    """
    def run(self,*args):
        pass_to_django_manage([execname, 'test'] + list(args))

class Shell(VerdiCommand):
    """
    Runs the interactive shell with the Django environment.

    This command runs the 'manage.py shell' command, that opens a
    IPython shell with the Django environment loaded.
    """
    def run(self,*args):
        pass_to_django_manage([execname, 'shell'] + list(args))

    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""

class Test(VerdiCommand):
    """
    Runs all aiida tests.

    This will run both the django tests for the db application, plus
    the unittests of a few aida modules.
    If you want to limit the tests to a specific subset of modules,
    pass them as further parameters. Without parameters, all tests are
    run. An invalid parameter will make the code print the list of all
    valid parameters.
    """

    # TODO: add all test folders
    allowed_test_folders = ['aida.scheduler', 'aida.transport']

    def run(self,*args):
        import unittest

        test_folders = []
        do_db = False
        if args:
            for arg in args:
                if arg in self.allowed_test_folders:
                    test_folders.append(arg)
                elif arg == 'db':
                    do_db = True
                else:
                    print >> sys.stderr, (
                        "{} is not a valid test folder. "
                        "Allowed test folders are:".format(arg))
                    print >> sys.stderr, "\n".join(
                        '  * {}'.format(a) for a in self.allowed_test_folders)
                    print >> sys.stderr, '  * db'
                    sys.exit(1)
        else:
            # Without arguments, run all tests
            test_folders = self.allowed_test_folders
            do_db = True

        for test_folder in test_folders:
            print "v"*75
            print ">>> Tests for module {} <<<".format(test_folder.ljust(50))
            print "^"*75
            testsuite = unittest.defaultTestLoader.discover(
                test_folder,top_level_dir = os.path.dirname(aida.__file__))
            test_runner = unittest.TextTestRunner()
            test_runner.run( testsuite )

        if do_db:
            print "v"*75
            print (">>> Tests for django db application   "
                   "                                  <<<")
            print "^"*75
            pass_to_django_manage([execname, 'test', 'db'])

    def complete(self, subargs_idx, subargs):
        """
        I complete with subargs that were not used yet.
        """
        # I remove the one on which I am, so if I wrote all of it but
        # did not press space, it will get completed
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx+1:]
        # I create a list of the tests that are not already written on the 
        # command line
        remaining_tests = (
            set(self.allowed_test_folders + ['db']) - set(other_subargs))
        print " ".join(sorted(remaining_tests))

class Install(VerdiCommand):
    """
    Install/setup aida for the current user.

    This command creates the ~/.aida folder in the home directory 
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a syncdb + migrate command to create/setup the database.
    """
    def run(self,*args):

        create_base_dirs()
        create_configuration()

        print "Executing now a syncdb --migrate command..."
        pass_to_django_manage([execname, 'syncdb', '--migrate'])


########################################################################
# HERE ENDS THE COMMAND FUNCTION LIST
########################################################################
# From here on: utility functions

def pass_to_django_manage(argv):
    """
    Call the corresponding django manage.py command
    """
    from aida.common.utils import load_django
    import django.core.management
    
    load_django()
    django.core.management.execute_from_command_line(argv)

def get_listparams():
    """
    Return a string with the list of parameters, to be printed.
    
    The advantage of this function is that the calling routine can
    choose to print it on stdout or stderr, depending on the needs.
    """
    max_length = max(len(i) for i in short_doc.keys())

    name_desc = [(cmd.ljust(max_length+2), desc.strip()) 
                 for cmd, desc in short_doc.iteritems()]

    name_desc = sorted(name_desc)
    
    return ("List of available commands:" + os.linesep +
            os.linesep.join(["  * {} {}".format(name, desc) 
                             for name, desc in name_desc]))


def get_command_suggestion(command):
    """
    A function that prints on stderr a list of similar commands
    """ 
    import difflib 

    similar_cmds = difflib.get_close_matches(command, short_doc.keys())
    if similar_cmds:
        print >> sys.stderr, ""
        print >> sys.stderr, "Did you mean this?"
        print >> sys.stderr, "\n".join(["     {}".format(i)
                                        for i in similar_cmds])

def install_daemon_files(aida_dir, daemon_dir, log_dir, aida_user):
    daemon_conf_file = "aida_daemon.conf"

    aida_module_dir = os.path.split(os.path.abspath(aida.__file__))[0]

    daemon_conf = """
[unix_http_server]
file="""+daemon_dir+"""/supervisord.sock   ; (the path to the socket file)

[supervisord]
logfile="""+log_dir+"""/supervisord.log 
logfile_maxbytes=10MB 
logfile_backups=2         
loglevel=info                
pidfile="""+daemon_dir+"""/supervisord.pid
nodaemon=false               
minfds=1024                 
minprocs=200                 

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///"""+daemon_dir+"""/supervisord.sock 

;=======================================
; Main AIDA Deamon
;=======================================

[program:aida-daemon]
command=python """+aida_module_dir+"""/djsite/manage.py celeryd --loglevel=INFO
directory="""+daemon_dir+"""
user="""+aida_user+"""
numprocs=1
stdout_logfile="""+log_dir+"""/aida_daemon.log
stderr_logfile="""+log_dir+"""/aida_daemon.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=30
process_name=%(process_num)s

; ==========================================
; AIDA Deamon BEAT - for scheduled tasks
; ==========================================
[program:aida-daemon-beat]
command=python """+aida_module_dir+"""/djsite/manage.py celerybeat
directory="""+daemon_dir+"""
user="""+aida_user+"""
numprocs=1
stdout_logfile="""+log_dir+"""/aida_daemon_beat.log
stderr_logfile="""+log_dir+"""/aida_daemon_beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs = 30
process_name=%(process_num)s
"""

    with open(os.path.join(aida_dir,daemon_dir,daemon_conf_file), "w") as f:
        f.write(daemon_conf)

def create_base_dirs():
    # For the daemon, to be hard-coded when ok
    daemon_subdir    = "daemon"
    log_dir          = "daemon/log"
    
    aida_dir        = os.path.expanduser("~/.aida") 
    aida_daemon_dir = os.path.join(aida_dir,daemon_subdir)
    aida_log_dir    = os.path.join(aida_dir,log_dir)
    aida_user       = getpass.getuser()
  
    if (not os.path.isdir(aida_dir)):
        os.makedirs(aida_dir)
    
    if (not os.path.isdir(aida_daemon_dir)):
        os.makedirs(aida_daemon_dir)
      
    if (not os.path.isdir(aida_log_dir)):
        os.makedirs(aida_log_dir)
        
    # Install daemon files 
    install_daemon_files(aida_dir, aida_daemon_dir, aida_log_dir, aida_user)

def create_configuration():
    import readline
    from aida.common.utils import store_config, get_config, backup_config
      
    aida_dir = os.path.expanduser("~/.aida")
    
    try:
        confs = get_config()
        backup_config()
    except ConfigurationError:
        # No configuration file found
        confs = {}  
      
    try:
        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get('AIDADB_ENGINE','sqlite3')))
        confs['AIDADB_ENGINE'] = raw_input('Database engine: ')

        if 'sqlite' in confs['AIDADB_ENGINE']:
            confs['AIDADB_ENGINE'] = 'sqlite3'          
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_NAME', os.path.join(aida_dir,"aida.db"))))
            confs['AIDADB_NAME'] = raw_input('AIDA Database location: ')
            confs['AIDADB_HOST'] = ""
            confs['AIDADB_PORT'] = ""
            confs['AIDADB_USER'] = ""
            confs['AIDADB_PASS'] = ""

        elif 'postgre' in confs['AIDADB_ENGINE']:
            confs['AIDADB_ENGINE'] = 'postgresql_psycopg2'
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_HOST','localhost')))
            confs['AIDADB_HOST'] = raw_input('PostgreSQL host: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_PORT','5432')))
            confs['AIDADB_PORT'] = raw_input('PostgreSQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_NAME','aidadb')))
            confs['AIDADB_NAME'] = raw_input('AIDA Database name: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_USER','aida_user')))
            confs['AIDADB_USER'] = raw_input('AIDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_PASS','aida_password')))
            confs['AIDADB_PASS'] = raw_input('AIDA Database password: ')

        elif 'mysql' in confs['AIDADB_ENGINE']:
            confs['AIDADB_ENGINE'] = 'mysql'
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_NAME','localhost')))
            confs['AIDADB_HOST'] = raw_input('mySQL host: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_PORT','3306')))
            confs['AIDADB_PORT'] = raw_input('mySQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_NAME','aidadb')))
            confs['AIDADB_NAME'] = raw_input('AIDA Database name: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_USER','aida_user')))
            confs['AIDADB_USER'] = raw_input('AIDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIDADB_PASS','aida_password')))
            confs['AIDADB_PASS'] = raw_input('AIDA Database password: ')
        else:
            raise ValueError("You have to specify a database !")

        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get('AIDADB_REPOSITORY',
                          os.path.join(aida_dir,"repository/"))))
        confs['AIDADB_REPOSITORY'] = raw_input('AIDA repository directory: ')
        if (not os.path.isdir(confs['AIDADB_REPOSITORY'])):
            os.makedirs(confs['AIDADB_REPOSITORY'])

        store_config(confs)
    finally:
        readline.set_startup_hook(lambda: readline.insert_text(""))
   
def exec_from_cmdline(argv):
    """
    The main function to be called. Pass as paramater the sys.argv.
    """
    import os

    ### This piece of code takes care of creating a list of valid
    ### commands and of their docstrings for dynamic management of
    ### the code.
    ### It defines a few global variables

    global execname
    global list_commands
    global short_doc
    global long_doc

    # import itself
    from aida.cmdline import verdilib
    import inspect

    # Retrieve the list of commands
    verdilib_namespace = verdilib.__dict__

    list_commands ={k.lower(): v for k, v in verdilib_namespace.iteritems()
                    if inspect.isclass(v) and not v==VerdiCommand and 
                    issubclass(v,VerdiCommand)}

    # Retrieve the list of docstrings, managing correctly the 
    # case of empty docstrings. Each value is a list of lines
    raw_docstrings = {k: (v.__doc__ if v.__doc__ else "").splitlines()
                       for k, v in list_commands.iteritems()}

    short_doc = {}
    long_doc = {}
    for k, v in raw_docstrings.iteritems():
        lines = [l.strip() for l in v] 
        empty_lines = [bool(l) for l in lines]
        try:
            first_idx = empty_lines.index(True) # The first non-empty line
        except ValueError:
            # All False
            short_doc[k] = "No description available"
            log_doc[k] = ""
            continue
        short_doc[k] = lines[first_idx]
        long_doc[k]  = os.linesep.join(lines[first_idx+1:])

    execname = os.path.basename(argv[0])

    try:
        command = argv[1]
    except IndexError:
        print >> sys.stderr,  "Usage: {} COMMAND [<args>]".format(execname)
        print >> sys.stderr, ""
        print >> sys.stderr, get_listparams()
        print >> sys.stderr, "See '{} help' for more help.".format(execname)
        sys.exit(1)
        
    if command in list_commands:
        CommandClass = list_commands[command]()
        CommandClass.run(*argv[2:])
    else:
        print >> sys.stderr, ("{}: '{}' is not a valid command. "
            "See '{} help' for more help.".format(execname, command, execname))
        get_command_suggestion(command)
        sys.exit(1)
    
