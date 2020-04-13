# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=unused-argument
"""Unit tests for editing pre and post bash scripts, comments, etc."""
import pytest

from aiida.cmdline.utils.multi_line_input import edit_pre_post, edit_comment

COMMAND = 'sleep 1 ; vim -c "g!/^#=/s/$/Test" -cwq'  # Appends `Test` to every line NOT starting with `#=`


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_pre_post(non_interactive_editor):
    result = edit_pre_post(summary={'Param 1': 'Value 1', 'Param 2': 'Value 1'})
    assert result[0] == 'Test\nTest\nTest'
    assert result[1] == 'Test\nTest\nTest'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_pre_post(non_interactive_editor):
    result = edit_pre_post(pre='OldPre', post='OldPost')
    assert result[0] == 'Test\nOldPreTest\nTest'
    assert result[1] == 'Test\nOldPostTest\nTest'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_pre_post_comment(non_interactive_editor):
    """Test that lines starting with '#=' are ignored and are not ignored if they start with any other character."""
    result = edit_pre_post(pre='OldPre\n#=Delete me', post='OldPost #=Dont delete me')
    assert result[0] == 'Test\nOldPreTest\nTest'
    assert result[1] == 'Test\nOldPost #=Dont delete meTest\nTest'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_pre_bash_comment(non_interactive_editor):
    """Test that bash comments starting with '#' are NOT deleted."""
    result = edit_pre_post(pre='OldPre\n# Dont delete me', post='OldPost # Dont delete me')
    assert result[0] == 'Test\nOldPreTest\n# Dont delete meTest\nTest'
    assert result[1] == 'Test\nOldPost # Dont delete meTest\nTest'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_new_comment(non_interactive_editor):
    new_comment = edit_comment()
    assert new_comment == 'Test'


@pytest.mark.parametrize('non_interactive_editor', (COMMAND,), indirect=True)
def test_edit_comment(non_interactive_editor):
    old_comment = 'OldComment'
    new_comment = edit_comment(old_cmt=old_comment)
    assert new_comment == old_comment + 'Test'
