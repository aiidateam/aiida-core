# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments, wrong-import-position
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi` command line interface."""
from __future__ import absolute_import
import click_completion

# Activate the completion of parameter types provided by the click_completion package
click_completion.init()

# Import to populate the `verdi` sub commands
from aiida.cmdline.commands import (cmd_calculation, cmd_code, cmd_comment, cmd_completioncommand, cmd_computer,
                                    cmd_data, cmd_database, cmd_daemon, cmd_devel, cmd_export, cmd_graph, cmd_group,
                                    cmd_import, cmd_node, cmd_process, cmd_profile, cmd_quicksetup, cmd_rehash,
                                    cmd_restapi, cmd_run, cmd_setup, cmd_shell, cmd_user, cmd_work, cmd_workflow)

# Import to populate the `verdi data` sub commands
from aiida.cmdline.commands.cmd_data import (cmd_array, cmd_bands, cmd_cif, cmd_parameter, cmd_remote, cmd_structure,
                                             cmd_trajectory, cmd_upf)
