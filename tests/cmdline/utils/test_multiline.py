###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for editing pre and post bash scripts, comments, etc."""

import click
import pytest

from aiida.cmdline.utils.multi_line_input import edit_comment, edit_multiline_template

COMMAND = 'sleep 1 ; vim -c "g!/^#=/s/$/Test" -cwq'  # Appends `Test` to every line NOT starting with `#=`


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_new_comment(non_interactive_editor):
    new_comment = edit_comment()
    assert new_comment == 'Test'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_comment(non_interactive_editor):
    old_comment = 'OldComment'
    new_comment = edit_comment(old_cmt=old_comment)
    assert new_comment == f'{old_comment}Test'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_multiline_template_empty(non_interactive_editor, monkeypatch):
    """Test ``edit_multiline_template`` returns empty string when `click.edit` returns empty value e.g. ``None``."""

    def edit(*args, **kwargs):
        return None

    monkeypatch.setattr(click, 'edit', edit)

    assert edit_multiline_template(template_name='multiline.tpl') == ''


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_multiline_template(non_interactive_editor):
    """Test ``edit_multiline_template`` returns empty string when `click.edit` returns empty value e.g. ``None``."""
    # The template will contain two empty lines, and those will get `Test` appended to it
    assert edit_multiline_template(template_name='multiline.tpl') == 'Test\nTest'
