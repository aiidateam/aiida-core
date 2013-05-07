"""
Command line commands for the main executable 'verdi' of aiida

If you want to define a new command line parameter, just define a new
function whose name starts with cmd_NAME and accepts a variable-length
number of parameters (the command-line parameters),
which will be invoked when this executable is called as
verdi NAME

Don't forget to add the docstring: the first line will be the
short description, the following ones the long description.

## TODO: implement bash completion
"""
import sys
import os
import getpass

import aida
from aida.common.exceptions import ConfigurationError

# default execname; can be substituted later in the call from
# exec_from_cmdline
execname = 'verdi'

# prefix for command functions
command_prefix = "cmd_"

########################################################################
# HERE STARTS THE COMMAND FUNCTION LIST
########################################################################

def cmd_listparamsshort(*args):
    """
    List available commands in short format.

    List available commands on stdout, all on the same line, separated by
    spaces. Useful for scripting (e.g., bash completion).
    """
    print " ".join(list_commands)

def cmd_listparams(*args):
    """
    List available commands.

    List available commands and their short description.
    For the long description, use the 'help' command.
    """
    print get_listparams()

def cmd_help(*args):
    """
    Describe a specific command.

    Pass a further argument to get a description of a given command.
    """
    try:
        command = args[0]
    except IndexError:
        cmd_listparams()
        print >> sys.stderr, ""
        print >> sys.stderr, ("Use '{} help <command>' for more information "
                              "on a specific command.".format(execname))
        sys.exit(1)

    try:
        command_index = list_commands.index(command)
        print "Description for '%s %s'" % (execname, command)
        print ""
        print "**", short_cmd_descriptions[command_index]
        if long_cmd_descriptions[command_index]:
            print long_cmd_descriptions[command_index]
    except IndexError:
        print >> sys.stderr, (
            "{}: '{}' is not a recognized command.".format(execname, command))
        sys.exit(1)

def cmd_syncdb(*args):
    """
    Create new tables in the database.

    This command calls the Django 'manage.py syncdb' command to create
    new tables in the database, and possibly install triggers.
    Pass a --migrate option to automatically also migrate the tables
    managed using South migrations.
    """
    pass_to_django_manage([execname, 'syncdb'] + list(args))

def cmd_migrate(*args):
    """
    Migrates the tables in the database to the most recent schema.

    This command calls the Django 'manage.py migrate' command to migrate
    tables managed by django-south to their most recent version.
    """
    pass_to_django_manage([execname, 'migrate'] + list(args))

def cmd_djangotests(*args):
    """
    Runs the django tests.

    This command calls the Django 'manage.py test' command to run the
    unittests of django. Pass the name of an application to restrict
    the tests to those of the specific application.
    """
    pass_to_django_manage([execname, 'test'] + list(args))

def cmd_shell(*args):
    """
    Runs the interactive shell with the Django environment loaded.

    This command runs the 'manage.py shell' command, that opens a
    IPython shell with the Django environment loaded.
    """
    pass_to_django_manage([execname, 'shell'] + list(args))

def cmd_daemon(*args):
    """
    Manage the aida daemon.

    This command allows to start, stop or restart the aida daemon,
    and to inquire its status.
    """
    # TODO: move code here?

    pass_to_django_manage([execname, 'daemon'] + list(args))

def cmd_test(*args):
    """
    Runs all aiida tests.

    This will run both the django tests for the db application, plus
    the unittests of a few aida modules.
    If you want to limit the tests to a specific subset of modules,
    pass them as further parameters. Without parameters, all tests are
    run. An invalid parameter will make the code print the list of all
    valid parameters.
    """
    import unittest

    # TODO: add all test folders

    allowed_test_folders = ['aida.scheduler', 'aida.transport']

    test_folders = []
    do_db = False
    if args:
        for arg in args:
            if arg in allowed_test_folders:
                test_folders.append(arg)
            elif arg == 'db':
                do_db = True
            else:
                print >> sys.stderr, (
                    "{} is not a valid test folder. "
                    "Allowed test folders are:".format(arg))
                print >> sys.stderr, "\n".join(
                    '  * {}'.format(a) for a in allowed_test_folders)
                print >> sys.stderr, '  * db'
    else:
        # Without arguments, run all tests
        test_folders = allowed_test_folders
        do_db = True

    for test_folder in test_folders:
        print "v"*75
        print ">>> Tests for module {} <<<".format(test_folder.ljust(50))
        print "^"*75
        testsuite = unittest.defaultTestLoader.discover(test_folder)
        test_runner = unittest.TextTestRunner()
        test_runner.run( testsuite )

    if do_db:
        print "v"*75
        print (">>> Tests for django db application   "
               "                                  <<<")
        print "^"*75
        pass_to_django_manage([execname, 'test', 'db'])

def cmd_install(*args):
    """
    Install/setup aida for the current user.

    This command creates the ~/.aida folder in the home directory 
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a syncdb + migrate command to create/setup the database.
    """
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
    max_length = max(len(i) for i in list_commands)

    name_desc = [(cmd.ljust(max_length+2), desc.split('\n')[0]) 
                 for cmd, desc in zip(list_commands, short_cmd_descriptions)]

    name_desc = sorted(name_desc)
    
    return ("List of available commands:\n" +
            "\n".join(["  * %s %s" % i for i in name_desc]))


def get_command_suggestion(command):
    """
    A function that prints on stderr a list of similar commands
    """ 
    import difflib 

    similar_cmds = difflib.get_close_matches(command, list_commands)
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
    global list_docstrings
    global description_lines
    global short_cmd_descriptions
    global long_cmd_descriptions

    # import itself
    from aida.cmdline import verdilib

    # Retrieve the list of commands
    verdilib_namespace = verdilib.__dict__
    list_commands = [c[len(command_prefix):] for c in verdilib_namespace.keys()
                     if c.startswith(command_prefix)]
    # Retrieve the list of docstrings, managing correctly the 
    # case of empty docstrings.
    list_docstrings = [verdilib_namespace[command_prefix+c].func_doc 
                       for c in list_commands]
    list_docstrings = [d if d else "No description available." 
                       for d in list_docstrings]

    description_lines = [[l.strip() for l in d.split('\n')] 
                         for d in list_docstrings] 

    # I remove empty lines at the beginning
    for desc_idx in range(len(description_lines)):
        for idx, l in enumerate(description_lines[desc_idx]):
            if l.strip(): # non-empty line
                break
        description_lines[desc_idx] = description_lines[desc_idx][idx:]

    # I obtain short and long command line descriptions
    short_cmd_descriptions = [d[0] for d in description_lines]
    long_cmd_descriptions = ["\n".join(d[1:]) for d in description_lines]


    execname = os.path.basename(argv[0])

    try:
        command = argv[1]
    except IndexError:
        print >> sys.stderr,  "Usage: {} COMMAND [<args>]".format(execname)
        print >> sys.stderr, ""
        print >> sys.stderr, get_listparams()
        sys.exit(1)
        
    if command in list_commands:
        verdilib_namespace[command_prefix+command](*argv[2:])
    else:
        print >> sys.stderr, ("{}: '{}' is not a valid command. "
            "See '{} help' for more help."(execname, command, execname))
        get_command_suggestion(command)
        sys.exit(1)
    
