# -*- coding: utf-8 -*-
"""Module that defines methods required to setup a new AiiDA instance."""
from __future__ import absolute_import

import os


def create_instance_directories():
    """Create the base directories required for a new AiiDA instance.

    This will create the base AiiDA directory defined by the AIIDA_CONFIG_FOLDER variable, unless it already exists.
    Subsequently, it will create the daemon directory within it and the daemon log directory.
    """
    from .settings import AIIDA_CONFIG_FOLDER, DAEMON_DIR, DAEMON_LOG_DIR, DEFAULT_UMASK

    directory_base = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    directory_daemon = os.path.join(directory_base, DAEMON_DIR)
    directory_daemon_log = os.path.join(directory_base, DAEMON_LOG_DIR)

    umask = os.umask(DEFAULT_UMASK)

    try:
        if not os.path.isdir(directory_base):
            os.makedirs(directory_base)

        if not os.path.isdir(directory_daemon):
            os.makedirs(directory_daemon)

        if not os.path.isdir(directory_daemon_log):
            os.makedirs(directory_daemon_log)
    finally:
        os.umask(umask)
