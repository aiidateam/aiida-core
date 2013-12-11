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

    * status: inquire the status of the deamon.

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

    def get_daemon_pid(self):
        """
        Return the daemon pid, as read from the supervisord.pid file.
        Return None if no pid is found (or the pid is not valid).
        """
        
        if (os.path.isfile(os.path.join(
                    aiida_dir,daemon_subdir,"supervisord.pid"))):
            try:
                return int(open(
                        os.path.join(aiida_dir, daemon_subdir,
                                     "supervisord.pid"), 'r').read().strip())
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
            print "Deamon already running, try ask for status"
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
            
    def daemon_stop(self):
        """
        Stop the daemon
        """
        from signal import SIGTERM

        pid = self.get_daemon_pid()
        if (pid==None):
            print "Deamon not running (cannot find the PID for it)"
            return

        print "Shutting down AiiDA Daemon ({})...".format(pid)
        try:
            os.kill(pid, SIGTERM)
        except OSError as e:
            if e.errno == 3: # No such process
                print ("The process {} was not found! "
                    "Assuming it was already stopped.".format(pid))
            else:
                raise
            
    def daemon_status(self):
        """
        Print the status of the daemon
        """
        import supervisor
        import supervisor.supervisorctl
        import xmlrpclib

        pid = self.get_daemon_pid()
        if (pid==None):
            print "Deamon not running (cannot find the PID for it)"
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
                print "The deamon is shutting down..."
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
                print "* {:<30} {:<10} {}".format(
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
            print "Deamon not running (cannot find the PID for it)"
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
        import time 
        
        pid = self.get_daemon_pid()
        if pid is not None:
            self.daemon_stop()
            
        max_retries = 10
            
        restarted = False
        for _ in range(max_retries):
            print "Waiting for the AiiDA Deamon to shutdown..."
            pid = self.get_daemon_pid()
            if (pid==None):
                self.daemon_start()
                restarted = True
                break
            else:        
                # Wait two seconds between retries
                time.sleep(2)

        if not restarted:
            print ("Unable to restart (the old daemon took too much time to "
                   "shut down).")
            print "Check the status and restart manually."
