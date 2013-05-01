from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.core.management import call_command
import aida
import os
import getpass

daemon_subdir    = "daemon"
daemon_conf_file = "aida_daemon.conf"
log_dir          = "daemon/log"

def install_daemon_files(aida_dir, daemon_dir, log_dir, aida_user):

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
serverurl=unix:///"""+daemon_dir+"""/supervisor.sock 

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

class Command(BaseCommand):

    def handle(self, *args, **options):

      # python manage.py migrate djcelery
      #call_command('syncdb', interactive=True)

      aida_dir        = os.path.expanduser("~/.aida") #os.path.abspath(aida.__path__[0])
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


