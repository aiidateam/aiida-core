from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import os
import aida
import subprocess
from signal import signal, SIGTERM
import time 
from aida.common.utils import get_config

daemon_subdir    = "daemon"
daemon_conf_file = "aida_daemon.conf"
log_dir          = "daemon/log"

class Command(BaseCommand):

    #aida_dir = os.path.abspath(aida.__path__[0])
    aida_dir        = os.path.expanduser("~/.aida")
    
    option_list = BaseCommand.option_list + (
        make_option('--start',
            action='store_true',
            dest='start',
            help='Starting AIDA Deamon'),
        make_option('--stop',
            action='store_true',
            dest='stop',
            help='Stopping AIDA Deamon'),
        make_option('--status',
            action='store_true',
            dest='status',
            help='Get the AIDA Daemon status'),
        make_option('--restart',
            action='store_true',
            dest='restart',
            help='Restart the AIDA Daemon'),
        )

    def getDaemonPid(self):

        if (os.path.isfile(os.path.join(self.aida_dir,daemon_subdir,"supervisord.pid"))):
            return int(open(os.path.join(self.aida_dir,daemon_subdir,"supervisord.pid"), 'r').read().strip())
        else:
            return None


    def start(self):
        
        self.stdout.write("Starting AIDA Daemon ...")

        process = subprocess.Popen("supervisord -c "+ \
            os.path.join(self.aida_dir,daemon_subdir,"aida_daemon.conf"), 
            shell=True, stdout=subprocess.PIPE)
        process.wait()
        if (process.returncode==0):
            self.stdout.write("Daemon started")

    def stop(self, pid):

        self.stdout.write("Shutting down AIDA Daemon ("+str(pid)+")...")
        os.kill(pid, SIGTERM)
        

    def status(self, pid):

        process = subprocess.Popen("supervisorctl -c "+ \
            os.path.join(self.aida_dir,daemon_subdir,"aida_daemon.conf")+" avail", 
            shell=True, stdout=subprocess.PIPE)

        process.wait()
        self.stdout.write(process.stdout.read())

    def handle(self, *args, **options):

      pid = self.getDaemonPid()

      if options['start']:

        if (not pid==None):
            self.stdout.write("Deamon already running, try ask for status")
            return
        else:
            self.start()
        
      elif options['stop']:

        if (pid==None):
            self.stdout.write("Deamon not running (cannot find the PID for it)")
            return
        else:
            self.stop(pid)

      elif options['status']:

        if (pid==None):
            self.stdout.write("Deamon not running (cannot find the PID for it)")
            return
        else:
            self.status(pid)

      elif options['restart']:

        if (not pid==None):
            self.stop(pid)

        for i in range(10):
            self.stdout.write("Waiting for the AIDA Deamon to shutdown...")
            pid = self.getDaemonPid()
            if (pid==None):
                self.start()
                break
            else:        
                time.sleep(1)

        

