#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import getpass
import os

import aiida.common.setup as setup



class Migration(object):
    """
    This class converts the configuration from the AiiDA 0.6.0 version (Django)
    to version 0.7.0 (Django).

    It is assumed that it is already (correctly) defined the place that the
    various configuration files are found in the aiida.common.setup.
    """

    DAEMON_CONF_FILE = "aiida_daemon.conf"

    # The default umask for file creation under AIIDA_CONFIG_FOLDER
    DEFAULT_UMASK = 0077

    def __init__(self):
        # Profile key
        self._profiles_key = "profiles"

    def install_daemon_files(aiida_dir, daemon_dir, log_dir, local_user):
        """
        Install the files needed to run the daemon.
        """
        daemon_conf = """
[unix_http_server]
file={daemon_dir}/supervisord.sock   ; (the path to the socket file)

[supervisord]
logfile={log_dir}/supervisord.log
logfile_maxbytes=10MB
logfile_backups=2
loglevel=info
pidfile={daemon_dir}/supervisord.pid
nodaemon=false
minfds=1024
minprocs=200

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///{daemon_dir}/supervisord.sock

;=======================================
; Main AiiDA Daemon
;=======================================
[program:aiida-daemon]
command=celery worker -A tasks --loglevel=INFO --beat --schedule={daemon_dir}/celerybeat-schedule
directory={aiida_code_home}/daemon/
user={local_user}
numprocs=1
stdout_logfile={log_dir}/aiida_daemon.log
stderr_logfile={log_dir}/aiida_daemon.log
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; When resorting to send SIGKILL to the program to terminate it
; send SIGKILL to its whole process group instead,
; taking care of its children as well.
killasgroup=true

; Set Celery priority higher than default (999)
; so, if rabbitmq is supervised, it will start first.
priority=1000
"""

        old_umask = os.umask(DEFAULT_UMASK)
        try:
            with open(os.path.join(aiida_dir, daemon_dir, DAEMON_CONF_FILE),
                      "w") as f:
                f.write(
                    daemon_conf.format(daemon_dir=daemon_dir, log_dir=log_dir,
                                       local_user=local_user,
                                       aiida_code_home=os.path.split(
                                           os.path.abspath(
                                               aiida.__file__))[0]))
        finally:
            os.umask(old_umask)

    def perform_migration(self):
        # Backup the previous config
        setup.backup_config()
        # Get the AiiDA directory path
        aiida_directory = os.path.expanduser(setup.AIIDA_CONFIG_FOLDER)
        # Construct the daemon directory path
        daemon_dir = os.path.join(aiida_directory, setup.DAEMON_SUBDIR)
        # Construct the log directory path
        log_dir = os.path.join(aiida_directory, setup.LOG_SUBDIR)
        # Update the daemon directory
        setup.install_daemon_files(aiida_directory, daemon_dir, log_dir,
                             getpass.getuser(),
                                   daemon_conf=self.curr_daemon_conf)

if __name__ == '__main__':
    Migration().perform_migration()
    print("Migration finished.")
