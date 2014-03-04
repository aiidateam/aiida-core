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
"""
import sys
import os
import getpass

import aiida
from aiida.common.exceptions import ConfigurationError
from aiida.cmdline.baseclass import VerdiCommand
from aiida.cmdline import pass_to_django_manage

## Import here from other files; once imported, it will be found and
## used as a command-line parameter
from aiida.cmdline.commands.daemon import Daemon
from aiida.cmdline.commands.computer import Computer
from aiida.cmdline.commands.workflow import Workflow
from aiida.cmdline.commands.upf import Upf
from aiida.cmdline.commands.code import Code
from aiida.cmdline.commands.calculation import Calculation
from aiida.cmdline.commands.devel import Devel

from aiida.cmdline import execname

########################################################################
# HERE STARTS THE COMMAND FUNCTION LIST
########################################################################

class CompletionCommand(VerdiCommand):
    """
    Return the bash completion function to put in ~/.bashrc

    This command prints on screen the function to be inserted in 
    your .bashrc command. You can copy and paste the output, or simply
    add 
    eval "`verdi completioncommand`"
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
    Manage bash completion 

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
    List available commands

    List available commands and their short description.
    For the long description, use the 'help' command.
    """
    
    def run(self,*args):
        print get_listparams()

class Help(VerdiCommand):
    """
    Describe a specific command

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
    
    
class Install(VerdiCommand):
    """
    Install/setup aiida for the current user

    This command creates the ~/.aiida folder in the home directory 
    of the user, interactively asks for the database settings and
    the repository location, does a setup of the daemon and runs
    a syncdb command to create/setup the database.
    """
    def run(self,*args):

        create_base_dirs()
        create_configuration()

        #print "Executing now a syncdb --migrate command..."
        #pass_to_django_manage([execname, 'syncdb', '--migrate'])
        print "Executing now a syncdb command..."
        pass_to_django_manage([execname, 'syncdb'])

    
    
class SyncDB(VerdiCommand):
    """
    Create new tables in the database

    This command calls the Django 'manage.py syncdb' command to create
    new tables in the database, and possibly install triggers.
    Pass a --migrate option to automatically also migrate the tables
    managed using South migrations.
    """

    def run(self,*args):
        pass_to_django_manage([execname, 'syncdb'] + list(args))

#class Migrate(VerdiCommand):
#    """
#    Migrate tables and data using django-south
#    
#    This command calls the Django 'manage.py migrate' command to migrate
#    tables managed by django-south to their most recent version.
#    """
#    def run(self,*args):
#        pass_to_django_manage([execname, 'migrate'] + list(args))

class Shell(VerdiCommand):
    """
    Run the interactive shell with the Django environment

    This command runs the 'manage.py shell' command, that opens a
    IPython shell with the Django environment loaded.
    """
    def run(self,*args):
        pass_to_django_manage([execname, 'shell'] + list(args))

    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""

class GoToComputer(VerdiCommand):
    """
    Open a shell to the calc folder on the cluster

    This command runs the 'manage.py shell' command, that opens a
    IPython shell with the Django environment loaded.
    """
    def run(self,*args):
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Node, Calculation
        from aiida.common.utils import load_django
        
        try:
            calc_id = args[0]
        except IndexError:
            print >> sys.stderr, "Pass as further argument a calculation ID or UUID."
            sys.exit(1)
        try:
            pk=int(calc_id)
            is_pk=True
        except ValueError:
            uuid = calc_id
            is_pk=False

        print "Loading environment..."
        load_django()

        try:
            if is_pk:
                calc = Node.get_subclass_from_pk(pk)
            else:
                calc = Node.get_subclass_from_pk(uuid)
        except NotExistent:
            print >> sys.stderr, "No node exists with ID={}.".format(calc_id)
            sys.exit(1)

        if not isinstance(calc,Calculation):
            print >> sys.stderr, "Node with ID={} is not a calculation; it is a {}".format(
                calc_id, calc.__class__.__name__)
            sys.exit(1)

        # get the transport
        try:
            t = calc._get_transport()
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        # get the remote directory
        remotedir = calc.get_remote_workdir()
        if not remotedir:
            print >> sys.stderr, "No remote work directory is set for this calculation!"
            sys.exit(1)
        
        # get the command to run (does not require to open the connection!)
        cmd_to_run = t.gotocomputer_command(remotedir)
        # Connect (execute command)
        print "Going the the remote folder..."
        #print cmd_to_run
        os.system(cmd_to_run)
        
    def complete(self, subargs_idx, subargs):
        # disable further completion
        print ""


        
class Runserver(VerdiCommand):
    """
    Run the AiiDA webserver on localhost.

    This command runs the webserver on the default port. Further command line
    options are passed to the Django manage runserver command 
    """
    def run(self,*args):
        pass_to_django_manage([execname, 'runserver'] + list(args))


########################################################################
# HERE ENDS THE COMMAND FUNCTION LIST
########################################################################
# From here on: utility functions

def get_listparams():
    """
    Return a string with the list of parameters, to be printed
    
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

def install_daemon_files(aiida_dir, daemon_dir, log_dir, aiida_user):
    daemon_conf_file = "aiida_daemon.conf"

    aiida_module_dir = os.path.split(os.path.abspath(aiida.__file__))[0]

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
; Main AiiDA Daemon
;=======================================

[program:aiida-daemon]
command=python """+aiida_module_dir+"""/djsite/manage.py celeryd --loglevel=INFO
directory="""+daemon_dir+"""
user="""+aiida_user+"""
numprocs=1
stdout_logfile="""+log_dir+"""/aiida_daemon.log
stderr_logfile="""+log_dir+"""/aiida_daemon.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=30
process_name=%(process_num)s

; ==========================================
; AiiDA Deamon BEAT - for scheduled tasks
; ==========================================
[program:aiida-daemon-beat]
command=python """+aiida_module_dir+"""/djsite/manage.py celerybeat
directory="""+daemon_dir+"""
user="""+aiida_user+"""
numprocs=1
stdout_logfile="""+log_dir+"""/aiida_daemon_beat.log
stderr_logfile="""+log_dir+"""/aiida_daemon_beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs = 30
process_name=%(process_num)s
"""

    with open(os.path.join(aiida_dir,daemon_dir,daemon_conf_file), "w") as f:
        f.write(daemon_conf)

def create_base_dirs():
    # For the daemon, to be hard-coded when ok
    daemon_subdir    = "daemon"
    log_dir          = "daemon/log"
    
    aiida_dir        = os.path.expanduser("~/.aiida") 
    aiida_daemon_dir = os.path.join(aiida_dir,daemon_subdir)
    aiida_log_dir    = os.path.join(aiida_dir,log_dir)
    aiida_user       = getpass.getuser()
  
    if (not os.path.isdir(aiida_dir)):
        os.makedirs(aiida_dir)
    
    if (not os.path.isdir(aiida_daemon_dir)):
        os.makedirs(aiida_daemon_dir)
      
    if (not os.path.isdir(aiida_log_dir)):
        os.makedirs(aiida_log_dir)
        
    # Install daemon files 
    install_daemon_files(aiida_dir, aiida_daemon_dir, aiida_log_dir, aiida_user)

def create_configuration():
    import readline
    from aiida.common.utils import store_config, get_config, backup_config
      
    aiida_dir = os.path.expanduser("~/.aiida")
    
    try:
        confs = get_config()
        backup_config()
    except ConfigurationError:
        # No configuration file found
        confs = {}  
      
    try:
        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get('AIIDADB_ENGINE','sqlite3')))
        confs['AIIDADB_ENGINE'] = raw_input('Database engine: ')

        if 'sqlite' in confs['AIIDADB_ENGINE']:
            confs['AIIDADB_ENGINE'] = 'sqlite3'          
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME', os.path.join(aiida_dir,"aiida.db"))))
            confs['AIIDADB_NAME'] = raw_input('AiiDA Database location: ')
            confs['AIIDADB_HOST'] = ""
            confs['AIIDADB_PORT'] = ""
            confs['AIIDADB_USER'] = ""
            confs['AIIDADB_PASS'] = ""

        elif 'postgre' in confs['AIIDADB_ENGINE']:
            confs['AIIDADB_ENGINE'] = 'postgresql_psycopg2'
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_HOST','localhost')))
            confs['AIIDADB_HOST'] = raw_input('PostgreSQL host: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_PORT','5432')))
            confs['AIIDADB_PORT'] = raw_input('PostgreSQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME','aiidadb')))
            confs['AIIDADB_NAME'] = raw_input('AiiDA Database name: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_USER','aiida_user')))
            confs['AIIDADB_USER'] = raw_input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_PASS','aiida_password')))
            confs['AIIDADB_PASS'] = raw_input('AiiDA Database password: ')

        elif 'mysql' in confs['AIIDADB_ENGINE']:
            confs['AIIDADB_ENGINE'] = 'mysql'
            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME','localhost')))
            confs['AIIDADB_HOST'] = raw_input('mySQL host: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_PORT','3306')))
            confs['AIIDADB_PORT'] = raw_input('mySQL port: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_NAME','aiidadb')))
            confs['AIIDADB_NAME'] = raw_input('AiiDA Database name: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_USER','aiida_user')))
            confs['AIIDADB_USER'] = raw_input('AiiDA Database user: ')

            readline.set_startup_hook(lambda: readline.insert_text(
                    confs.get('AIIDADB_PASS','aiida_password')))
            confs['AIIDADB_PASS'] = raw_input('AiiDA Database password: ')
        else:
            raise ValueError("You have to specify a database !")

        readline.set_startup_hook(lambda: readline.insert_text(
                confs.get('AIIDADB_REPOSITORY',
                          os.path.join(aiida_dir,"repository/"))))
        confs['AIIDADB_REPOSITORY'] = raw_input('AiiDA repository directory: ')
        if (not os.path.isdir(confs['AIIDADB_REPOSITORY'])):
            os.makedirs(confs['AIIDADB_REPOSITORY'])

        store_config(confs)
    finally:
        readline.set_startup_hook(lambda: readline.insert_text(""))
   
def exec_from_cmdline(argv):
    """
    The main function to be called. Pass as paramater the sys.argv.
    """
    ### This piece of code takes care of creating a list of valid
    ### commands and of their docstrings for dynamic management of
    ### the code.
    ### It defines a few global variables

    global execname
    global list_commands
    global short_doc
    global long_doc

    # import itself
    from aiida.cmdline import verdilib
    import inspect

    # Retrieve the list of commands
    verdilib_namespace = verdilib.__dict__

    list_commands ={v.get_command_name(): v for v in verdilib_namespace.itervalues()
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
            long_doc[k] = ""
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
    
