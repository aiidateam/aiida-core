###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Basic tests for the alembic_cli module."""

from click.testing import CliRunner

from aiida.storage.psql_dos.alembic_cli import alembic_cli


def test_history():
    """Test the 'history' command."""
    runner = CliRunner()
    result = runner.invoke(alembic_cli, ['history'])
    assert result.exit_code == 0, result.output
    assert 'head' in result.output
