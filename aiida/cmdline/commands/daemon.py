import sys
import os
import subprocess

from aiida.cmdline.baseclass import VerdiCommand

daemon_subdir    = "daemon"
daemon_conf_file = "aiida_daemon.conf"
log_dir          = "daemon/log"
aiida_dir = os.path.expanduser("~/.aiida")  

conffname = os.path.join(aiida_dir,daemon_subdir,daemon_conf_file)


class Daemon(VerdiCommand):
    """
    Manage the AiiDA daemon
    
    This command allows to interact with the AiiDA daemon.
    Valid subcommands are:

    * start: start the daemon

    * stop: restart the daemon

    * restart: restart the aiida daemon, waiting for it to cleanly exit\
        before restarting it.

    * status: inquire the status of the Daemon.

    * showlog: show the log in a continuous fashion, similar to the 'tail -f' \
        command. Press CTRL+C to exit.
    """


    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        start, stop, status and restart.
        """
        self.valid_subcommands = {
            'start': self.daemon_start,
            'stop' : self.daemon_stop,
            'status': self.daemon_status,
            'showlog': self.daemon_showlog,
            'restart': self.daemon_restart,
            }

    def run(self,*args):       
        """
        Run the specified daemon subcommand.
        """
        try:
            function_to_call = self.valid_subcommands.get(
                args[0], self.invalid_subcommand)
        except IndexError:
            function_to_call = self.no_subcommand
            
        function_to_call()

    def complete(self,subargs_idx, subargs):
        """
        Complete the daemon subcommand.
        """
        if subargs_idx == 0:
            print "\n".join(self.valid_subcommands.keys())
        else:
            print ""

    def _get_pid_full_path(self):
        """
        Return the full path of the supervisord.pid file.
        """
        return os.path.normpath(
            os.path.join(aiida_dir,daemon_subdir,"supervisord.pid"))

    def _get_sock_full_path(self):
        """
        Return the full path of the supervisord.sock file.
        """
        return os.path.normpath(
            os.path.join(aiida_dir,daemon_subdir,"supervisord.sock"))

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

    def no_subcommand(self):
        print >> sys.stderr, ("You have to pass a valid subcommand to "
                              "'daemon'. Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def invalid_subcommand(self,*args):
        print >> sys.stderr, ("You passed an invalid subcommand to 'daemon'. "
                              "Valid subcommands are:")
        print >> sys.stderr, "\n".join("  {}".format(sc) 
                                       for sc in self.valid_subcommands)
        sys.exit(1)

    def daemon_start(self):
        """
        Start the daemon
        """
        pid = self.get_daemon_pid()

        if pid is not None:
            print "Daemon already running, try ask for status"
            return
        
        print "Loading Django ..."
        from aiida.common.utils import load_django
        load_django()
        
        print "Clearing all locks ..."
        from aiida.orm.lock import LockManager
        LockManager().clear_all()
        
        print "Starting AiiDA Daemon ..."
        process = subprocess.Popen(
            "supervisord -c {}".format(conffname), 
            shell=True, stdout=subprocess.PIPE)
        process.wait()
        if (process.returncode==0):
            print "Daemon started"
            
    def daemon_stop(self, wait_for_death=True):
        """
        Stop the daemon.
        
        :param wait_for_death: If True, also verifies that the process was already
            killed. It attempts at most ``max_retries`` times, with ``sleep_between_retries``
            seconds between one attempt and the following one (both variables are
            for the time being hardcoded in the function).
            
        :return: None if ``wait_for_death`` is False. True/False if the process was
            actually dead or after all the retries it was still alive.
        """
        from signal import SIGTERM
        import time
        import errno

        max_retries = 20
        sleep_between_retries = 3

        pid = self.get_daemon_pid()
        if pid is None:
            print "Daemon not running (cannot find the PID for it)"
            return

        print "Shutting down AiiDA Daemon ({})...".format(pid)
        try:
            os.kill(pid, SIGTERM)
        except OSError as e:
            if e.errno == errno.ESRCH: # No such process
                print ("The process {} was not found! "
                    "Assuming it was already stopped.".format(pid))
                print "Cleaning the .pid and .sock files..."
                self._clean_sock_files()
            else:
                raise
        
        dead = None
        if wait_for_death:
            dead = False
            restarted = False
            for _ in range(max_retries):
                pid = self.get_daemon_pid()
                if pid is None:
                    dead = True
                    print "AiiDA Daemon was correctly shut down."
                    break
                else:        
                    print "Waiting for the AiiDA Daemon to shutdown..."
                    # Wait two seconds between retries
                    time.sleep(sleep_between_retries)
            if not dead:
                print ("Unable to stop (the daemon took too much time to "
                       "shut down).")
                print ("Probably, it is in the middle of a long operation.")
                print ("The shut down signal was sent, anyway, so it should "
                       "shut down soon.")
            
        return dead
            
    def daemon_status(self):
        """
        Print the status of the daemon
        """
        import supervisor
        import supervisor.supervisorctl
        import xmlrpclib

        pid = self.get_daemon_pid()
        if (pid==None):
            print "Daemon not running (cannot find the PID for it)"
            return

        c = supervisor.supervisorctl.ClientOptions()
        s = c.read_config(conffname)
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
            print "## Found {} processes running:".format(len(running_processes))
            for process in running_processes:
                print "* {:<22} {:<10} {}".format(
                    "{}[{}]".format(process['group'], process['name']),
                    process['statename'], process['description'])
        else:
            print "I was able to connect to the daemon, but I did not find any process..."
        
    def daemon_showlog(self):
        """
        Show the log of the daemon, press CTRL+C to quit.
        """
        pid = self.get_daemon_pid()
        if (pid==None):
            print "Daemon not running (cannot find the PID for it)"
            return

        try:
            process = subprocess.Popen(
               "supervisorctl -c {} tail -f aiida-daemon:0".format(
                           conffname),
                               shell=True) #, stdout=subprocess.PIPE)
            process.wait()
        except KeyboardInterrupt:
            # exit on CTRL+C
            process.kill()
 
    def daemon_restart(self):
        """
        Restart the daemon. Before restarting, wait for the daemon to really
        shut down.
        """
        pid = self.get_daemon_pid()
        if pid is not None:
            dead = self.daemon_stop(wait_for_death=True)
            
        if not dead:
            print "Check the status and, when the daemon will be down, "
            print "you can restart it using:"
            print "    verdi daemon start"
        else:
            self.daemon_start()


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
            if e.errno != errno.ENOENT: # No such file
                raise 

        try:
            os.remove(self._get_pid_full_path())
        except OSError as e:
            # Ignore if errno = errno.ENOENT (2): no file found 
            if e.errno != errno.ENOENT: # No such file
                raise 
        