# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Configuration file for pytest tests."""
import pytest  # pylint: disable=unused-import

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # pylint: disable=invalid-name


@pytest.fixture()
def non_interactive_editor(request):
    """Fixture to patch click's `Editor.edit_file`.

    In `click==7.1` the `Editor.edit_file` command was changed to escape the `os.environ['EDITOR']` command. Our tests
    are currently abusing this variable to define an automated vim command in order to make an interactive command
    non-interactive, and escaping it makes bash interpret the command and its arguments as a single command instead.
    Here we patch the method to remove the escaping of the editor command.

    :param request: the command to set for the editor that is to be called
    """
    import os
    from unittest.mock import patch
    from click._termui_impl import Editor

    os.environ['EDITOR'] = request.param
    os.environ['VISUAL'] = request.param

    def edit_file(self, filename):
        import os
        import subprocess
        import click

        editor = self.get_editor()
        if self.env:
            environ = os.environ.copy()
            environ.update(self.env)
        else:
            environ = None
        try:
            process = subprocess.Popen(
                '{} {}'.format(editor, filename),  # This is the line that we change removing `shlex_quote`
                env=environ,
                shell=True,
            )
            exit_code = process.wait()
            if exit_code != 0:
                raise click.ClickException('{}: Editing failed!'.format(editor))
        except OSError as exception:
            raise click.ClickException('{}: Editing failed: {}'.format(editor, exception))

    with patch.object(Editor, 'edit_file', edit_file):
        yield
