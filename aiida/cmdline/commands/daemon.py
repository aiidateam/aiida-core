import sys
import os
import subprocess

from aiida.cmdline.baseclass import VerdiCommand

daemon_subdir    = "daemon"
daemon_conf_file = "aiida_daemon.conf"
log_dir          = "daemon/log"
aiida_dir = os.path.expanduser("~/.aiida")  

class Daemon(VerdiCommand):
    """
    Manage the AiiDA daemon
    
    This command allows to interact with the AiiDA daemon.
    Valid subcommands are:
    * start: start the daemon
    * stop: restart the daemon
    * restart: restart the aiida daemon, waiting for it to cleanly exit
        before restarting it.
    * status: inquire the status of the deamon.
    * showlog: show the log in a continuous fashion, similar to the 'tail -f' 
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

    def invalid_subcommand(self):
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

        print "Starting AiiDA Daemon ..."
        process = subprocess.Popen(
            "supervisord -c {}".format(os.path.join(
                    aiida_dir,daemon_subdir,"aiida_daemon.conf")), 
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
        os.kill(pid, SIGTERM)
        
    def daemon_status(self):
        """
        Print the status of the daemon
        """
        pid = self.get_daemon_pid()
        if (pid==None):
            print "Deamon not running (cannot find the PID for it)"
            return

        process = subprocess.Popen("supervisorctl -c {} avail".format(
                os.path.join(aiida_dir,daemon_subdir,"aiida_daemon.conf")),
                                   shell=True, stdout=subprocess.PIPE)
        process.wait()
        print process.stdout.read()

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
                   os.path.join(aiida_dir,daemon_subdir,"aiida_daemon.conf")),
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
