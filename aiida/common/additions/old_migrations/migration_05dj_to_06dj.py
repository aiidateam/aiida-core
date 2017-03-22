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

import aiida
import aiida.common.setup as setup



class Migration(object):
    """
    This class converts the configuration from the AiiDA version with one
    backend (Django) as it is described in commit e048939 (version to to the implementation
    that supports DJango and SQLAlchemy.

    It is assumed that it is already (correctly) defined the place that the
    various configuration files are found in the aiida.common.setup.
    """
    DAEMON_CONF_FILE = "aiida_daemon.conf"

    # The default umask for file creation under AIIDA_CONFIG_FOLDER
    DEFAULT_UMASK = 0077

    def __init__(self):
        # Profile key
        self._profiles_key = "profiles"

    def install_daemon_files(self, aiida_dir, daemon_dir, log_dir, local_user):
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
command=python "{aiida_module_dir}/backends/djsite/manage.py" --aiida-process=daemon celeryd --loglevel=INFO
directory={daemon_dir}
user={local_user}
numprocs=1
stdout_logfile={log_dir}/aiida_daemon.log
stderr_logfile={log_dir}/aiida_daemon.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=30
process_name=%(process_num)s

; ==========================================
; AiiDA Deamon BEAT - for scheduled tasks
; ==========================================
[program:aiida-daemon-beat]
command=python "{aiida_module_dir}/backends/djsite/manage.py" --aiida-process=daemon celerybeat
directory={daemon_dir}
user={local_user}
numprocs=1
stdout_logfile={log_dir}/aiida_daemon_beat.log
stderr_logfile={log_dir}/aiida_daemon_beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs = 30
process_name=%(process_num)s
"""
        old_umask = os.umask(self.DEFAULT_UMASK)
        try:
            with open(os.path.join(aiida_dir, daemon_dir, self.DAEMON_CONF_FILE),
                      "w") as f:
                f.write(
                    daemon_conf.format(daemon_dir=daemon_dir, log_dir=log_dir,
                                       local_user=local_user,
                                       aiida_module_dir=
                                       os.path.split(os.path.abspath(
                                           aiida.__file__))[0]))
        finally:
            os.umask(old_umask)

    def adding_backend(self):
        """
        Gets the main AiiDA configuration and searches if there is a backend
        defined. If there isn't any then Django is added.
        """
        # Get the available configuration
        conf = setup.get_config()

        # Identifying all the available profiles
        if self._profiles_key in conf.keys():
            profiles = conf[self._profiles_key]
            p_keys = profiles.keys()
            # For every profile
            for p_key in p_keys:
                # get the
                curr_profile = profiles[p_key]

                # Check if there is a specific backend in the profile
                # and if not, add Django as backend
                if setup.aiidadb_backend_key not in curr_profile.keys():
                    curr_profile[setup.aiidadb_backend_key] = \
                        setup.aiidadb_backend_value_django

        # Returning the configuration
        return conf



    def perform_migration(self):
        # Backup the previous config
        setup.backup_config()
        # Get the AiiDA directory path
        aiida_directory = os.path.expanduser(setup.AIIDA_CONFIG_FOLDER)
        # Construct the daemon directory path
        daemon_dir = os.path.join(aiida_directory, setup.DAEMON_SUBDIR)
        # Construct the log directory path
        log_dir = os.path.join(aiida_directory, setup.LOG_SUBDIR)
        # Update the configuration if needed
        confs = self.adding_backend()
        # Store the configuration
        setup.store_config(confs)
        # Update the daemon directory
        self.install_daemon_files(aiida_directory, daemon_dir, log_dir,
                             getpass.getuser())

if __name__ == '__main__':
    Migration().perform_migration()
    print("Migration finished.")
