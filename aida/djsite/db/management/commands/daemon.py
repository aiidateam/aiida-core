from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import install
import os
import aida
import subprocess
from signal import signal, SIGTERM

class Command(BaseCommand):

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
        )

    def getDaemonPid(self):

        aida_dir = os.path.abspath(aida.__path__[0])
        if (os.path.isfile(os.path.join(aida_dir,install.daemon_subdir,"supervisord.pid"))):
            return int(open(os.path.join(aida_dir,install.daemon_subdir,"supervisord.pid"), 'r').read().strip())
        else:
            return None


    def handle(self, *args, **options):

      aida_dir = os.path.abspath(aida.__path__[0])
      pid = self.getDaemonPid()

      if options['start']:

        if (not pid==None):
            self.stdout.write("Deamon already running, try ask for status")
            return

        self.stdout.write("Starting AIDA Daemon ...")

        process = subprocess.Popen("supervisord -c "+ \
            os.path.join(aida_dir,install.daemon_subdir,"aida_daemon.conf"), 
            shell=True, stdout=subprocess.PIPE)
        process.wait()
        if (process.returncode==0):
            self.stdout.write("Daemon started")
        

      elif options['stop']:

        if (pid==None):
            self.stdout.write("Deamon not running (cannot find the PID for it)")
            return

        self.stdout.write("Shutting down AIDA Daemon ("+str(pid)+")...")

        os.kill(pid, SIGTERM)
        

      elif options['status']:

        if (pid==None):
            self.stdout.write("Deamon not running (cannot find the PID for it)")
            return

        process = subprocess.Popen("supervisorctl -c "+ \
            os.path.join(aida_dir,install.daemon_subdir,"aida_daemon.conf")+" avail", 
            shell=True, stdout=subprocess.PIPE)

        process.wait()
        self.stdout.write(process.stdout.read())
