# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys
import os
import subprocess
from datetime import timedelta
from aiida.common import aiidalogger
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands


from aiida.backends.utils import is_dbenv_loaded
logger = aiidalogger.getChild('workflowmanager')


def is_daemon_user():
    """
    Return True if the user is the current daemon user, False otherwise.
    """
    from aiida.backends.utils import get_daemon_user
    from aiida.common.utils import get_configured_user_email

    daemon_user = get_daemon_user()
    this_user = get_configured_user_email()

    return daemon_user == this_user


def _get_env_with_venv_bin():
    pybin = os.path.dirname(sys.executable)
    currenv = os.environ.copy()
    currenv['PATH'] = pybin + ':' + currenv['PATH']
    return currenv

class Daemon(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA daemon

    This command allows to interact with the AiiDA daemon.
    Valid subcommands are:

    * start: start the daemon

    * stop: restart the daemon

    * restart: restart the aiida daemon, waiting for it to cleanly exit\
        before restarting it.

    * status: inquire the status of the Daemon.

    * logshow: show the log in a continuous fashion, similar to the 'tail -f' \
        command. Press CTRL+C to exit.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        start, stop, status and restart.
        """
        from aiida.common import setup

        self.valid_subcommands = {
            'start': (self.daemon_start, self.complete_none),
            'stop': (self.daemon_stop, self.complete_none),
            'status': (self.daemon_status, self.complete_none),
            'logshow': (self.daemon_logshow, self.complete_none),
            'restart': (self.daemon_restart, self.complete_none),
            'configureuser': (self.configure_user, self.complete_none),
        }

        self.conffile_full_path = os.path.expanduser(os.path.join(
                setup.AIIDA_CONFIG_FOLDER,
                setup.DAEMON_SUBDIR,
                setup.DAEMON_CONF_FILE
            ))

    def _get_pid_full_path(self):
        """
        Return the full path of the supervisord.pid file.
        """
        from aiida.common import setup

        return os.path.normpath(os.path.expanduser(
            os.path.join(setup.AIIDA_CONFIG_FOLDER,
                         setup.DAEMON_SUBDIR, "supervisord.pid")))

    def _get_sock_full_path(self):
        """
        Return the full path of the supervisord.sock file.
        """
        from aiida.common import setup

        return os.path.normpath(os.path.expanduser(
            os.path.join(setup.AIIDA_CONFIG_FOLDER,
                         setup.DAEMON_SUBDIR, "supervisord.sock")))

    def get_daemon_pid(self):
        """
        Return the daemon pid, as read from the supervisord.pid file.
        Return None if no pid is found (or the pid is not valid).
        """
        if (os.path.isfile(self._get_pid_full_path())):
            try:
                return int(open(self._get_pid_full_path(), 'r').read().strip())
            except (ValueError, IOError):
                return None
        else:
            return None

    def daemon_start(self, *args):
        """
        Start the daemon
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv(process='daemon')

        from aiida.daemon.timestamps import get_last_daemon_timestamp,set_daemon_timestamp

        if args:
            print >> sys.stderr, (
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()))
            sys.exit(1)

        from aiida.backends.utils import get_daemon_user
        from aiida.common.utils import get_configured_user_email

        daemon_user = get_daemon_user()
        this_user = get_configured_user_email()


        if daemon_user != this_user:
            print "You are not the daemon user! I will not start the daemon."
            print "(The daemon user is '{}', you are '{}')".format(
                daemon_user, this_user)
            print ""
            print "** FOR ADVANCED USERS ONLY: **"
            print "To change the current default user, use 'verdi install --only-config'"
            print "To change the daemon user, use 'verdi daemon configureuser'"

            sys.exit(1)

        pid = self.get_daemon_pid()

        if pid is not None:
            print "Daemon already running, try asking for its status"
            return

        print "Clearing all locks ..."
        from aiida.orm.lock import LockManager

        LockManager().clear_all()

        print "Starting AiiDA Daemon ..."
        currenv = _get_env_with_venv_bin()
        process = subprocess.Popen(
            "supervisord -c {}".format(self.conffile_full_path),
            shell=True, stdout=subprocess.PIPE, env=currenv)
        process.wait()

        # The following lines are needed for the workflow_stepper
        # (re-initialize the timestamps used to lock the task, in case
        # it crashed for some reason).
        # TODO: remove them when the old workflow system will be
        # taken away.
        try:
            if (get_last_daemon_timestamp('workflow',when='stop')
                -get_last_daemon_timestamp('workflow',when='start'))<timedelta(0):
                logger.info("Workflow stop timestamp was {}; re-initializing "
                            "it to current time".format(
                            get_last_daemon_timestamp('workflow',when='stop')))
                print "Re-initializing workflow stepper stop timestamp"
                set_daemon_timestamp(task_name='workflow', when='stop')
        except TypeError:
            # when some timestamps are None (i.e. not present), we make
            # sure that at least the stop timestamp is defined
            print "Re-initializing workflow stepper stop timestamp"
            set_daemon_timestamp(task_name='workflow', when='stop')

        if (process.returncode == 0):
            print "Daemon started"


    def kill_daemon(self):
        """
        This is the actual call that kills the daemon.

        There are some print statements inside, but no sys.exit, so it is
        safe to be called from other parts of the code.
        """
        from signal import SIGTERM
        import errno

        pid = self.get_daemon_pid()
        if pid is None:
            print "Daemon not running (cannot find the PID for it)"
            return

        print "Shutting down AiiDA Daemon ({})...".format(pid)
        try:
            os.kill(pid, SIGTERM)
        except OSError as e:
            if e.errno == errno.ESRCH:  # No such process
                print ("The process {} was not found! "
                       "Assuming it was already stopped.".format(pid))
                print "Cleaning the .pid and .sock files..."
                self._clean_sock_files()
            else:
                raise

    def daemon_stop(self, *args, **kwargs):
        """
        Stop the daemon.

        :param wait_for_death: If True, also verifies that the process was already
            killed. It attempts at most ``max_retries`` times, with ``sleep_between_retries``
            seconds between one attempt and the following one (both variables are
            for the time being hardcoded in the function).

        :return: None if ``wait_for_death`` is False. True/False if the process was
            actually dead or after all the retries it was still alive.
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv(process='daemon')

        from aiida.daemon.timestamps import get_last_daemon_timestamp,set_daemon_timestamp

        if args:
            print >> sys.stderr, (
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()))
            sys.exit(1)
        wait_for_death = kwargs.get('wait_for_death', True)

        import time

        max_retries = 20
        sleep_between_retries = 3

        # Note: NO check here on the daemon user: allow the daemon to be shut
        # down if it was inadvertently left active and the setting was changed.
        self.kill_daemon()

        dead = None
        if wait_for_death:
            dead = False
            for _ in range(max_retries):
                pid = self.get_daemon_pid()
                if pid is None:
                    dead = True
                    print "AiiDA Daemon shut down correctly."
                    # The following lines are needed for the workflow_stepper
                    # (re-initialize the timestamps used to lock the task, in case
                    # it crashed for some reason).
                    # TODO: remove them when the old workflow system will be
                    # taken away.
                    try:
                        if (get_last_daemon_timestamp('workflow',when='stop')
                            -get_last_daemon_timestamp('workflow',when='start'))<timedelta(0):
                            logger.info("Workflow stop timestamp was {}; re-initializing"
                                        " it to current time".format(
                                        get_last_daemon_timestamp('workflow',when='stop')))
                            print "Re-initializing workflow stepper stop timestamp"
                            set_daemon_timestamp(task_name='workflow', when='stop')
                    except TypeError:
                        # when some timestamps are None (i.e. not present), we make
                        # sure that at least the stop timestamp is defined
                        print "Re-initializing workflow stepper stop timestamp"
                        set_daemon_timestamp(task_name='workflow', when='stop')
                    break
                else:
                    print "Waiting for the AiiDA Daemon to shut down..."
                    # Wait two seconds between retries
                    time.sleep(sleep_between_retries)
            if not dead:
                print ("Unable to stop (the daemon took too much time to "
                       "shut down).")
                print ("Probably, it is in the middle of a long operation.")
                print ("The shut down signal was sent, anyway, so it should "
                       "shut down soon.")

        return dead

    def daemon_status(self, *args):
        """
        Print the status of the daemon
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv(process='daemon')

        if args:
            print >> sys.stderr, (
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()))
            sys.exit(1)

        import supervisor
        import supervisor.supervisorctl
        import xmlrpclib

        from aiida.utils import timezone

        from aiida.daemon.timestamps import get_most_recent_daemon_timestamp
        from aiida.common.utils import str_timedelta
        from pytz import UTC

        most_recent_timestamp = get_most_recent_daemon_timestamp()

        if most_recent_timestamp is not None:
            timestamp_delta = (timezone.datetime.now(tz=UTC) -
                               most_recent_timestamp)
            print ("# Most recent daemon timestamp:{}".format(
                str_timedelta(timestamp_delta)))
        else:
            print ("# Most recent daemon timestamp: [Never]")

        pid = self.get_daemon_pid()
        if pid is None:
            print "Daemon not running (cannot find the PID for it)"
            return

        c = supervisor.supervisorctl.ClientOptions()
        s = c.read_config(self.conffile_full_path)
        proxy = xmlrpclib.ServerProxy('http://127.0.0.1',
                                      transport=supervisor.xmlrpc.SupervisorTransport(
                                          s.username, s.password, s.serverurl))
        try:
            running_processes = proxy.supervisor.getAllProcessInfo()
        except xmlrpclib.Fault as e:
            if e.faultString == "SHUTDOWN_STATE":
                print "The daemon is shutting down..."
                return
            else:
                raise
        except Exception as e:
            import socket
            if isinstance(e, socket.error):
                print "Could not reach the daemon, I got a socket.error: "
                print "  -> [Errno {}] {}".format(e.errno, e.strerror)
            else:
                print "Could not reach the daemon, I got a {}: {}".format(
                    e.__class__.__name__, e.message)
            print "You can try to stop the daemon and start it again."
            return

        if running_processes:
            print "## Found {} process{} running:".format(len(running_processes), '' if len(running_processes)==1 else 'es')
            for process in running_processes:
                print "   * {:<22} {:<10} {}".format(
                    "{}[{}]".format(process['group'], process['name']),
                    process['statename'], process['description'])
        else:
            print "I was able to connect to the daemon, but I did not find any process..."

    def daemon_logshow(self, *args):
        """
        Show the log of the daemon, press CTRL+C to quit.
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv(process='daemon')

        if args:
            print >> sys.stderr, (
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()))
            sys.exit(1)

        pid = self.get_daemon_pid()
        if (pid == None):
            print "Daemon not running (cannot find the PID for it)"
            return

        try:
            currenv = _get_env_with_venv_bin()
            process = subprocess.Popen(
                "supervisorctl -c {} tail -f aiida-daemon".format(
                    self.conffile_full_path),
                shell=True, env=currenv)  # , stdout=subprocess.PIPE)
            process.wait()
        except KeyboardInterrupt:
            # exit on CTRL+C
            process.kill()

    def daemon_restart(self, *args):
        """
        Restart the daemon. Before restarting, wait for the daemon to really
        shut down.
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv(process='daemon')

        if args:
            print >> sys.stderr, (
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()))
            sys.exit(1)

        from aiida.backends.utils import get_daemon_user
        from aiida.common.utils import get_configured_user_email

        daemon_user = get_daemon_user()
        this_user = get_configured_user_email()

        if daemon_user != this_user:
            print "You are not the daemon user! I will not restart the daemon."
            print "(The daemon user is '{}', you are '{}')".format(
                daemon_user, this_user)

            sys.exit(1)

        pid = self.get_daemon_pid()

        dead = True

        if pid is not None:
            dead = self.daemon_stop(wait_for_death=True)

        if not dead:
            print "Check the status and, when the daemon will be down, "
            print "you can restart it using:"
            print "    verdi daemon start"
        else:
            self.daemon_start()

    def configure_user(self, *args):
        """
        Configure the user that can run the daemon.
        """
        if not is_dbenv_loaded():
            from aiida.backends.utils import load_dbenv
            load_dbenv(process='daemon')

        if args:
            print >> sys.stderr, (
                "No arguments allowed for the '{}' command.".format(
                    self.get_full_command_name()))
            sys.exit(1)

        from aiida.utils import timezone
        from aiida.backends.utils import get_daemon_user, set_daemon_user
        from aiida.common.utils import (get_configured_user_email,
                                        query_yes_no, query_string)
        from aiida.daemon.timestamps import get_most_recent_daemon_timestamp
        from aiida.common.utils import str_timedelta
        from aiida.orm.user import User

        old_daemon_user = get_daemon_user()
        this_user = get_configured_user_email()

        print("> Current default user: {}".format(this_user))
        print("> Currently configured user who can run the daemon: {}".format(
            old_daemon_user))
        if old_daemon_user == this_user:
            print("  (therefore, at the moment you are the user who can run "
                  "the daemon)")
            pid = self.get_daemon_pid()
            if pid is not None:
                print("The daemon is running! I will not proceed.")
                sys.exit(1)
        else:
            print("  (therefore, you cannot run the daemon, at the moment)")

        most_recent_timestamp = get_most_recent_daemon_timestamp()

        print "*" * 76
        print "* {:72s} *".format("WARNING! Change this setting only if you "
                                  "are sure of what you are doing.")
        print "* {:72s} *".format("Moreover, make sure that the "
                                  "daemon is stopped.")

        if most_recent_timestamp is not None:
            timestamp_delta = timezone.now() - most_recent_timestamp
            last_check_string = (
                "[The most recent timestamp from the daemon was {}]"
                .format(str_timedelta(timestamp_delta)))
            print "* {:72s} *".format(last_check_string)

        print "*" * 76

        answer = query_yes_no("Are you really sure that you want to change "
                              "the daemon user?", default="no")
        if not answer:
            sys.exit(0)

        print ""
        print "Enter below the email of the new user who can run the daemon."
        new_daemon_user_email = query_string("New daemon user: ", None)

        found_users = User.search_for_users(email=new_daemon_user_email)
        if len(found_users) == 0:
            print("ERROR! The user you specified ({}) does "
                  "not exist in the database!!".format(new_daemon_user_email))
            print("The available users are {}".format(
                [_.email for _ in User.search_for_users()]))
            sys.exit(1)

        set_daemon_user(new_daemon_user_email)

        print "The new user that can run the daemon is now {} {}.".format(
            found_users[0].first_name, found_users[0].last_name)

    def _clean_sock_files(self):
        """
        Tries to remove the supervisord.pid and .sock files from the .aiida/daemon
        subfolder. This is typically needed when the computer is restarted with
        the daemon still on.
        """
        import errno

        try:
            os.remove(self._get_sock_full_path())
        except OSError as e:
            # Ignore if errno = errno.ENOENT (2): no file found
            if e.errno != errno.ENOENT:  # No such file
                raise

        try:
            os.remove(self._get_pid_full_path())
        except OSError as e:
            # Ignore if errno = errno.ENOENT (2): no file found
            if e.errno != errno.ENOENT:  # No such file
                raise
