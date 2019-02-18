# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the 'verdi code' command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os
import subprocess as sp
import traceback
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_code import (setup_code, delete, hide, reveal, relabel, code_list, show, code_duplicate)
from aiida.common.exceptions import NotExistent
from aiida import orm


# pylint: disable=missing-docstring
class TestVerdiCodeSetup(AiidaTestCase):
    """Tests for the 'verdi code setup' command."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiCodeSetup, cls).setUpClass(*args, **kwargs)
        orm.Computer(
            name='comp',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida').store()

    def setUp(self):
        self.comp = orm.Computer.objects.get(name='comp')

        self.cli_runner = CliRunner()
        self.this_folder = os.path.dirname(__file__)
        self.this_file = os.path.basename(__file__)

    def test_help(self):
        self.cli_runner.invoke(setup_code, ['--help'], catch_exceptions=False)

    def test_reachable(self):
        output = sp.check_output(['verdi', 'code', 'setup', '--help'])
        self.assertIn(b'Usage:', output)

    def test_interactive_remote(self):
        from aiida.orm import Code
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'interactive_remote'
        user_input = '\n'.join(
            [label, 'description', 'arithmetic.add', 'yes', self.comp.name, '/remote/abs/path'])
        result = self.cli_runner.invoke(setup_code, input=user_input)
        self.assertClickResultNoException(result)
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)

    def test_interactive_upload(self):
        from aiida.orm import Code
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'interactive_upload'
        user_input = '\n'.join(
            [label, 'description', 'arithmetic.add', 'no', self.this_folder, self.this_file])
        result = self.cli_runner.invoke(setup_code, input=user_input)
        self.assertIsNone(result.exception, result.output)
        self.assertIsInstance(Code.get_from_string('{}'.format(label)), Code)

    def test_noninteractive_remote(self):
        from aiida.orm import Code
        label = 'noninteractive_remote'
        options = [
            '--non-interactive', '--label={}'.format(label), '--description=description',
            '--input-plugin=arithmetic.add', '--on-computer', '--computer={}'.format(self.comp.name),
            '--remote-abs-path=/remote/abs/path'
        ]
        result = self.cli_runner.invoke(setup_code, options)
        self.assertClickResultNoException(result)
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)

    def test_noninteractive_upload(self):
        from aiida.orm import Code
        label = 'noninteractive_upload'
        options = [
            '--non-interactive', '--label={}'.format(label), '--description=description',
            '--input-plugin=arithmetic.add', '--store-in-db', '--code-folder={}'.format(self.this_folder),
            '--code-rel-path={}'.format(self.this_file)
        ]
        result = self.cli_runner.invoke(setup_code, options)
        self.assertClickResultNoException(result)
        self.assertIsInstance(Code.get_from_string('{}'.format(label)), Code)

    def test_mixed(self):
        from aiida.orm import Code
        label = 'mixed_remote'
        options = ['--description=description', '--on-computer', '--remote-abs-path=/remote/abs/path']
        user_input = '\n'.join([label, 'arithmetic.add', self.comp.name])
        result = self.cli_runner.invoke(setup_code, options, input=user_input)
        self.assertClickResultNoException(result)
        self.assertIsInstance(Code.get_from_string('{}@{}'.format(label, self.comp.name)), Code)


class TestVerdiCodeCommands(AiidaTestCase):
    """Testing verdi code commands.

    Testing everything besides `code setup`.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        from aiida import orm

        super(TestVerdiCodeCommands, cls).setUpClass(*args, **kwargs)
        orm.Computer(
            name='comp',
            hostname='localhost',
            transport_type='local',
            scheduler_type='direct',
            workdir='/tmp/aiida').store()

    def setUp(self):
        from aiida import orm
        self.comp = orm.Computer.objects.get(name='comp')

        try:
            code = orm.Code.get_from_string('code')
        except NotExistent:
            code = orm.Code(
                input_plugin_name='arithmetic.add',
                remote_computer_exec=[self.comp, '/remote/abs/path'],
            )
            code.label = 'code'
            code.description = 'desc'
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
        result = self.cli_runner.invoke(relabel, [str(self.code.pk), 'new_code'])
        self.assertIsNone(result.exception, result.output)
        from aiida.orm import load_node
        new_code = load_node(self.code.pk)
        self.assertEqual(new_code.label, 'new_code')

    def test_relabel_code_full(self):
        self.cli_runner.invoke(relabel, [str(self.code.pk), 'new_code@comp'])
        from aiida.orm import load_node
        new_code = load_node(self.code.pk)
        self.assertEqual(new_code.label, 'new_code')

    def test_relabel_code_full_bad(self):
        result = self.cli_runner.invoke(relabel, [str(self.code.pk), 'new_code@otherstuff'])
        self.assertIsNotNone(result.exception)

    def test_delete_one(self):
        result = self.cli_runner.invoke(delete, [str(self.code.pk)])
        self.assertIsNone(result.exception, result.output)

        with self.assertRaises(NotExistent):
            from aiida.orm import Code
            Code.get_from_string('code')

    def test_code_list(self):
        # set up second code 'code2'
        from aiida.orm import Code
        try:
            code = Code.get_from_string('code2')
        except NotExistent:
            code = Code(
                input_plugin_name='templatereplacer',
                remote_computer_exec=[self.comp, '/remote/abs/path'],
            )
            code.label = 'code2'
            code.store()

        options = [
            '-A', '-a', '-o', '--input-plugin=arithmetic.add', '--computer={}'.format(self.comp.name)
        ]
        result = self.cli_runner.invoke(code_list, options)
        self.assertIsNone(result.exception, result.output)
        self.assertTrue(str(self.code.pk) in result.output, 'PK of first code should be included')
        self.assertTrue('code2' not in result.output, 'label of second code should not be included')
        self.assertTrue('comp' in result.output, 'computer name should be included')

    def test_code_list_hide(self):
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

    def test_code_duplicate_interactive(self):
        os.environ['VISUAL'] = 'sleep 1; vim -cwq'
        os.environ['EDITOR'] = 'sleep 1; vim -cwq'
        label = 'code_duplicate_interactive'
        user_input = label + '\n\n\n\n\n\n'
        result = self.cli_runner.invoke(code_duplicate, [str(self.code.pk)], input=user_input, catch_exceptions=False)
        self.assertIsNone(result.exception, result.output)

        from aiida.orm import Code
        new_code = Code.get_from_string(label)
        self.assertEqual(self.code.description, new_code.description)
        self.assertEqual(self.code.get_prepend_text(), new_code.get_prepend_text())
        self.assertEqual(self.code.get_append_text(), new_code.get_append_text())

    def test_code_duplicate_non_interactive(self):
        label = 'code_duplicate_noninteractive'
        result = self.cli_runner.invoke(code_duplicate, ['--non-interactive', '--label=' + label, str(self.code.pk)])
        self.assertIsNone(result.exception, result.output)

        from aiida.orm import Code
        new_code = Code.get_from_string(label)
        self.assertEqual(self.code.description, new_code.description)
        self.assertEqual(self.code.get_prepend_text(), new_code.get_prepend_text())
        self.assertEqual(self.code.get_append_text(), new_code.get_append_text())
        self.assertEqual(self.code.get_input_plugin_name(), new_code.get_input_plugin_name())
