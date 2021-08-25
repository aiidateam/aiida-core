# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi devel``."""
from aiida.cmdline.commands import cmd_devel
from aiida.orm import Node


def test_run_sql(run_cli_command):
    """Test ``verdi devel run-sql``."""
    options = ['SELECT COUNT(*) FROM db_dbnode;']
    result = run_cli_command(cmd_devel.devel_run_sql, options)
    assert str(Node.objects.count()) in result.output, result.output
