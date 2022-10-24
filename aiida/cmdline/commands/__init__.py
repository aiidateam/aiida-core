# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Sub commands of the ``verdi`` command line interface.

The commands need to be imported here for them to be registered with the top-level command group.
"""
from aiida.cmdline.commands import (
    cmd_archive,
    cmd_calcjob,
    cmd_code,
    cmd_computer,
    cmd_config,
    cmd_daemon,
    cmd_data,
    cmd_database,
    cmd_devel,
    cmd_group,
    cmd_help,
    cmd_node,
    cmd_plugin,
    cmd_process,
    cmd_profile,
    cmd_rabbitmq,
    cmd_restapi,
    cmd_run,
    cmd_setup,
    cmd_shell,
    cmd_status,
    cmd_storage,
    cmd_user,
)
