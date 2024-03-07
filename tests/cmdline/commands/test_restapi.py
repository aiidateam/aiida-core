###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi restapi``."""
from aiida.cmdline.commands.cmd_restapi import restapi
from aiida.restapi import run_api


def test_run_restapi(run_cli_command, monkeypatch):
    """Test ``verdi restapi``."""

    def run_api_noop(*_, **__):
        pass

    monkeypatch.setattr(run_api, 'run_api', run_api_noop)

    options = ['--hostname', 'localhost', '--port', '6000', '--debug', '--wsgi-profile']
    run_cli_command(restapi, options, use_subprocess=False)


def test_help(run_cli_command):
    """Tests help text for restapi command."""
    result = run_cli_command(restapi, ['--help'])
    assert 'Usage' in result.output
