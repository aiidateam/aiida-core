#!/usr/bin/env python
from optparse import make_option 
import os
import getpass
import os
import sys
import aida 


# ONLY these commands are passed to the Django manager
filter_command_list = ['syncdb', 'daemon', 'migrate', 'test']

# For the daemon, to be hard-coded when ok
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

def create_base_dirs(dev_arg):
    
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
      
def create_configuration(dev_arg):
        

      import readline
      from aida.common.utils import store_config, get_config, backup_config
      
      aida_dir        = os.path.expanduser("~/.aida")
      
      try:
        confs = get_config()
        backup_config()
        
      except:
        confs = {}  
    
      def get_default(field, default):
          if field in confs:
              return confs[field]
          else:
              return default
          
      
          
      readline.set_startup_hook(lambda: readline.insert_text(get_default('DBENGINE','sqlite3')))
      confs['AIDADB_ENGINE'] = raw_input('Database engine: ')
      
      if 'sqlite' in confs['AIDADB_ENGINE']:
           
          confs['AIDADB_ENGINE'] = 'sqlite3'
           
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_NAME',os.path.join(aida_dir,"aida.db"))))
          confs['AIDADB_NAME'] = raw_input('AIDA Database location: ')
          
          confs['AIDADB_HOST'] = ""
          confs['AIDADB_PORT'] = ""
          confs['AIDADB_USER'] = ""
          confs['AIDADB_PASS'] = ""
          
      elif 'postgre' in confs['AIDADB_ENGINE']:
          
          confs['AIDADB_ENGINE'] = 'postgresql_psycopg2'
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_HOST','locahost')))
          confs['AIDADB_HOST'] = raw_input('PostgreSQL host: ')
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_PORT','5432')))
          confs['AIDADB_PORT'] = raw_input('PostgreSQL port: ')
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_NAME','aidadb')))
          confs['AIDADB_NAME'] = raw_input('AIDA Database name: ')
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_USER','aida_user')))
          confs['AIDADB_USER'] = raw_input('AIDA Database user: ')
      
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_PASS','aida_password')))
          confs['AIDADB_PASS'] = raw_input('AIDA Database user: ')

      elif 'mysql' in confs['AIDADB_ENGINE']:
          
          confs['AIDADB_ENGINE'] = 'mysql'
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_NAME','locahost')))
          confs['AIDADB_HOST'] = raw_input('PostgreSQL host: ')
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_PORT','3306')))
          confs['AIDADB_PORT'] = raw_input('PostgreSQL port: ')
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_NAME','aidadb')))
          confs['AIDADB_NAME'] = raw_input('AIDA Database name: ')
          
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_USER','aida_user')))
          confs['AIDADB_USER'] = raw_input('AIDA Database user: ')
      
          readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_PASS','aida_password')))
          confs['AIDADB_PASS'] = raw_input('AIDA Database user: ')
      
      else:
          raise Exception("You have to specify a database !")
      
      readline.set_startup_hook(lambda: readline.insert_text(get_default('AIDADB_REPOSITORY',os.path.join(aida_dir,"repository/"))))
      confs['AIDADB_REPOSITORY'] = raw_input('AIDA repository directory: ')
      if (not os.path.isdir(confs['AIDADB_REPOSITORY'])):
          os.makedirs(confs['AIDADB_REPOSITORY'])
          
      store_config(confs)
      
      readline.set_startup_hook(lambda: readline.insert_text(""))
      
def pass_to_django(argv):
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aida.djsite.settings.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(argv)

def print_help():
    
    print""
    print "AIDA Version XX"
    print"-----------------"
    print""
    print "install\t\tRun the installation procedures"
    print "daemon\t\tDaemon utilities"
    print "syncdb\t\tUpdate the database structure"
    print "migrate\t\tMigrate the database"
    print""
    
def main():
    
    #create_base_dirs();
    #create_configuration();
    if (len(sys.argv)==1):
       print_help()
       return
        
    cmd = sys.argv[1];
    if (cmd in filter_command_list):
        pass_to_django(sys.argv)
        
    elif "install" in cmd:
        arg = None
        if len(sys.argv)>2:
            arg = sys.argv[2]
        
        create_base_dirs(arg);
        create_configuration(arg);
        
        pass_to_django([sys.argv[0],'syncdb']);
        pass_to_django([sys.argv[0],'migrate']);
        
    elif "help" in cmd:
        print_help()
        
        
        
if __name__ == "__main__":
    main()
    

    
