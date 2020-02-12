# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments,wrong-import-position
"""The `verdi` command line interface."""
import click_completion

# Activate the completion of parameter types provided by the click_completion package
click_completion.init()

# Import to populate the `verdi` sub commands
from aiida.cmdline.commands import (
    cmd_calcjob, cmd_code, cmd_comment, cmd_completioncommand, cmd_computer, cmd_config, cmd_data, cmd_database,
    cmd_daemon, cmd_devel, cmd_export, cmd_graph, cmd_group, cmd_help, cmd_import, cmd_node, cmd_plugin, cmd_process,
    cmd_profile, cmd_rehash, cmd_restapi, cmd_run, cmd_setup, cmd_shell, cmd_status, cmd_user
)
