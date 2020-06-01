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
"""Tests for the 'verdi code' command."""
import os
import subprocess as sp
from textwrap import dedent

from click.testing import CliRunner
import pytest

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_code import (setup_code, delete, hide, reveal, relabel, code_list, show, code_duplicate)
from aiida.common.exceptions import NotExistent
from aiida import orm


class TestVerdiCodeSetup(AiidaTestCase):
    """Tests for the 'verdi code setup' command."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.computer = orm.Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida'
        ).store()

    def setUp(self):
        self.cli_runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

    def test_help(self):
        self.cli_runner.invoke(setup_code, ['--help'], catch_exceptions=False)

    def test_reachable(self):
        output = sp.check_output(['verdi', 'code', 'setup', '--help'])
        self.assertIn(b'Usage:', output)

    def test_noninteractive_remote(self):
        """Test non-interactive remote code setup."""
        label = 'noninteractive_remote'
        options = [
            '--non-interactive', '--label={}'.format(label), '--description=description',
            '--input-plugin=arithmetic.add', '--on-computer', '--computer={}'.format(self.computer.name),
            '--remote-abs-path=/remote/abs/path'
        ]
        result = self.cli_runner.invoke(setup_code, options)
        self.assertClickResultNoException(result)
        self.assertIsInstance(orm.Code.get_from_string('{}@{}'.format(label, self.computer.name)), orm.Code)

    def test_noninteractive_upload(self):
        """Test non-interactive code setup."""
        label = 'noninteractive_upload'
        options = [
            '--non-interactive', '--label={}'.format(label), '--description=description',
            '--input-plugin=arithmetic.add', '--store-in-db', '--code-folder={}'.format(self.this_folder),
            '--code-rel-path={}'.format(self.this_file)
        ]
        result = self.cli_runner.invoke(setup_code, options)
        self.assertClickResultNoException(result)
        self.assertIsInstance(orm.Code.get_from_string('{}'.format(label)), orm.Code)

    def test_from_config(self):
        """Test setting up a code from a config file"""
        import tempfile

        label = 'noninteractive_config'

        with tempfile.NamedTemporaryFile('w') as handle:
            handle.write(
                dedent(
                    """
                    ---
                    label: {label}
                    input_plugin: arithmetic.add
                    computer: {computer}
                    remote_abs_path: /remote/abs/path
                    """
                ).format(label=label, computer=self.computer.name)
            )
            handle.flush()
            result = self.cli_runner.invoke(
                setup_code,
                ['--non-interactive', '--config', os.path.realpath(handle.name)]
            )

        self.assertClickResultNoException(result)
        self.assertIsInstance(orm.Code.get_from_string('{}'.format(label)), orm.Code)


class TestVerdiCodeCommands(AiidaTestCase):
    """Testing verdi code commands.

    Testing everything besides `code setup`."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.computer = orm.Computer(
            name='comp', hostname='localhost', transport_type='local', scheduler_type='direct', workdir='/tmp/aiida'
        ).store()

    def setUp(self):
        try:
            code = orm.Code.get_from_string('code')
        except NotExistent:
            code = orm.Code(
                input_plugin_name='arithmetic.add',
                remote_computer_exec=[self.computer, '/remote/abs/path'],
            )
            code.label = 'code'
            code.description = 'desc'
            code.set_prepend_text('text to prepend')
            code.set_append_text('text to append')
            code.store()
        self.code = code

        self.cli_runner = CliRunner()

    def test_hide_one(self):
        result = self.cli_runner.invoke(hide, [str(self.code.pk)])
        self.assertIsNone(result.exception, result.output)

        self.assertTrue(self.code.hidden)

    def test_reveal_one(self):
        result = self.cli_runner.invoke(reveal, [str(self.code.pk)])
        self.assertIsNone(result.exception, result.output)

        self.assertFalse(self.code.hidden)

    def test_relabel_code(self):
        """Test force code relabeling."""
        result = self.cli_runner.invoke(relabel, [str(self.code.pk), 'new_code'])
        self.assertIsNone(result.exception, result.output)
        new_code = orm.load_node(self.code.pk)
        self.assertEqual(new_code.label, 'new_code')

    def test_relabel_code_full(self):
        self.cli_runner.invoke(relabel, [str(self.code.pk), 'new_code@comp'])
        new_code = orm.load_node(self.code.pk)
        self.assertEqual(new_code.label, 'new_code')

    def test_relabel_code_full_bad(self):
        result = self.cli_runner.invoke(relabel, [str(self.code.pk), 'new_code@otherstuff'])
        self.assertIsNotNone(result.exception)

    def test_code_delete_one_force(self):
        """Test force code deletion."""
        result = self.cli_runner.invoke(delete, [str(self.code.pk), '--force'])
        self.assertIsNone(result.exception, result.output)

        with self.assertRaises(NotExistent):
            orm.Code.get_from_string('code')

    def test_code_list(self):
        """Test code list command."""
        # set up second code 'code2'
        try:
            code = orm.Code.get_from_string('code2')
        except NotExistent:
            code = orm.Code(
                input_plugin_name='templatereplacer',
                remote_computer_exec=[self.computer, '/remote/abs/path'],
            )
            code.label = 'code2'
            code.store()

        options = ['-A', '-a', '-o', '--input-plugin=arithmetic.add', '--computer={}'.format(self.computer.name)]
        result = self.cli_runner.invoke(code_list, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(str(self.code.pk) in result.output, 'PK of first code should be included')
        self.assertTrue('code2' not in result.output, 'label of second code should not be included')
        self.assertTrue('comp' in result.output, 'computer name should be included')
        self.assertNotIn(result.output, '# No codes found matching the specified criteria.')

    def test_code_list_hide(self):
        """Test that hidden codes are shown (or not) properly."""
        self.code.hide()
        options = ['-A']
        result = self.cli_runner.invoke(code_list, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(self.code.full_label not in result.output, 'code should be hidden')

        options = ['-a']
        result = self.cli_runner.invoke(code_list, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(self.code.full_label in result.output, 'code should be shown')

    def test_code_show(self):
        result = self.cli_runner.invoke(show, [str(self.code.pk)])
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(str(self.code.pk) in result.output)

    def test_code_duplicate_non_interactive(self):
        """Test code duplication non-interactive."""
        label = 'code_duplicate_noninteractive'
        result = self.cli_runner.invoke(code_duplicate, ['--non-interactive', '--label=' + label, str(self.code.pk)])
        self.assertIsNone(result.exception, result.output)

        new_code = orm.Code.get_from_string(label)
        self.assertEqual(self.code.description, new_code.description)
        self.assertEqual(self.code.get_prepend_text(), new_code.get_prepend_text())
        self.assertEqual(self.code.get_append_text(), new_code.get_append_text())
        self.assertEqual(self.code.get_input_plugin_name(), new_code.get_input_plugin_name())


class TestVerdiCodeNoCodes(AiidaTestCase):
    """Test functionality when no codes been set up."""

    def setUp(self):
        self.cli_runner = CliRunner()

    def test_code_list_no_codes_error_message(self):
        result = self.cli_runner.invoke(code_list)
        self.assertEqual(1, result.output.count('# No codes found matching the specified criteria.'))


@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_interactive_remote(clear_database_before_test, aiida_localhost, non_interactive_editor):
    """Test interactive remote code setup."""
    label = 'interactive_remote'
    user_input = '\n'.join([label, 'description', 'arithmetic.add', 'yes', aiida_localhost.name, '/remote/abs/path'])
    result = CliRunner().invoke(setup_code, input=user_input)
    assert result.exception is None
    assert isinstance(orm.Code.get_from_string('{}@{}'.format(label, aiida_localhost.name)), orm.Code)


@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_interactive_upload(clear_database_before_test, aiida_localhost, non_interactive_editor):
    """Test interactive code setup."""
    label = 'interactive_upload'
    dirname = os.path.dirname(__file__)
    basename = os.path.basename(__file__)
    user_input = '\n'.join([label, 'description', 'arithmetic.add', 'no', dirname, basename])
    result = CliRunner().invoke(setup_code, input=user_input)
    assert result.exception is None
    assert isinstance(orm.Code.get_from_string('{}'.format(label)), orm.Code)


@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_mixed(clear_database_before_test, aiida_localhost, non_interactive_editor):
    """Test mixed (interactive/from config) code setup."""
    from aiida.orm import Code
    label = 'mixed_remote'
    options = ['--description=description', '--on-computer', '--remote-abs-path=/remote/abs/path']
    user_input = '\n'.join([label, 'arithmetic.add', aiida_localhost.name])
    result = CliRunner().invoke(setup_code, options, input=user_input)
    assert result.exception is None
    assert isinstance(Code.get_from_string('{}@{}'.format(label, aiida_localhost.name)), Code)


@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_code_duplicate_interactive(clear_database_before_test, aiida_local_code_factory, non_interactive_editor):
    """Test code duplication interactive."""
    label = 'code_duplicate_interactive'
    user_input = label + '\n\n\n\n\n\n'
    code = aiida_local_code_factory('arithmetic.add', '/bin/cat', label='code')
    result = CliRunner().invoke(code_duplicate, [str(code.pk)], input=user_input)
    assert result.exception is None, result.exception

    duplicate = orm.Code.get_from_string(label)
    assert code.description == duplicate.description
    assert code.get_prepend_text() == duplicate.get_prepend_text()
    assert code.get_append_text() == duplicate.get_append_text()


@pytest.mark.parametrize('non_interactive_editor', ('sleep 1; vim -cwq',), indirect=True)
def test_code_duplicate_ignore(clear_database_before_test, aiida_local_code_factory, non_interactive_editor):
    """Providing "!" to description should lead to empty description.

    Regression test for: https://github.com/aiidateam/aiida-core/issues/3770
    """
    label = 'code_duplicate_interactive'
    user_input = label + '\n!\n\n\n\n\n'
    code = aiida_local_code_factory('arithmetic.add', '/bin/cat', label='code')
    result = CliRunner().invoke(code_duplicate, [str(code.pk)], input=user_input, catch_exceptions=False)
    assert result.exception is None, result.exception

    duplicate = orm.Code.get_from_string(label)
    assert duplicate.description == ''
