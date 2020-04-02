# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi run`."""
import tempfile

from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_run


class TestVerdiRun(AiidaTestCase):
    """Tests for `verdi run`."""

    def setUp(self):
        super().setUp()
        self.cli_runner = CliRunner()

    def test_run_workfunction(self):
        """Regression test for #2165

        If the script that is passed to `verdi run` is not compiled correctly, running workfunctions from the script
        that are defined within the script will fail, as the inspect module will not correctly be able to determin
        the full path of the source file.
        """
        from aiida.orm import load_node
        from aiida.orm import WorkFunctionNode

        script_content = """
#!/usr/bin/env python
from aiida.engine import workfunction

@workfunction
def wf():
    pass

if __name__ == '__main__':
    result, node = wf.run_get_node()
    print(node.pk)
        """

        # If `verdi run` is not setup correctly, the script above when run with `verdi run` will fail, because when
        # the engine will try to create the node for the workfunction and create a copy of its sourcefile, namely the
        # script itself, it will use `inspect.getsourcefile` which will return None
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = [fhandle.name]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            # Try to load the function calculation node from the printed pk in the output
            pk = int(result.output)
            node = load_node(pk)

            # Verify that the node has the correct function name and content
            self.assertTrue(isinstance(node, WorkFunctionNode))
            self.assertEqual(node.function_name, 'wf')
            self.assertEqual(node.get_function_source_code(), script_content)


class TestAutoGroups(AiidaTestCase):
    """Test the autogroup functionality."""

    def setUp(self):
        """Setup the CLI runner to run command line commands."""
        from aiida.orm import autogroup

        super().setUp()
        self.cli_runner = CliRunner()
        # I need to disable the global variable of this test environment,
        # because invoke is just calling the function and therefore inheriting
        # the global variable
        self._old_autogroup = autogroup.CURRENT_AUTOGROUP
        autogroup.CURRENT_AUTOGROUP = None

    def tearDown(self):
        """Setup the CLI runner to run command line commands."""
        from aiida.orm import autogroup

        super().tearDown()
        autogroup.CURRENT_AUTOGROUP = self._old_autogroup

    def test_autogroup(self):
        """Check if the autogroup is properly generated."""
        from aiida.orm import QueryBuilder, Node, Group, load_node

        script_content = """from aiida.orm import Data
node = Data().store()
print(node.pk)
"""

        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = [fhandle.name]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )

    def test_autogroup_custom_label(self):
        """Check if the autogroup is properly generated with the label specified."""
        from aiida.orm import QueryBuilder, Node, Group, load_node

        script_content = """from aiida.orm import Data
node = Data().store()
print(node.pk)
"""
        autogroup_label = 'SOME_group_LABEL'
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = [fhandle.name, '--group-label-prefix', autogroup_label]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )
            self.assertEqual(all_auto_groups[0][0].label, autogroup_label)

    def test_no_autogroup(self):
        """Check if the autogroup is not generated if ``verdi run`` is asked not to."""
        from aiida.orm import QueryBuilder, Node, Group, load_node

        script_content = """from aiida.orm import Data
node = Data().store()
print(node.pk)
"""

        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = [fhandle.name, '--no-group']
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(len(all_auto_groups), 0, 'There should be no autogroup generated')

    def test_autogroup_filter_class(self):  # pylint: disable=too-many-locals
        """Check if the autogroup is properly generated but filtered classes are skipped."""
        from aiida.orm import QueryBuilder, Node, Group, load_node

        script_content = """from aiida.orm import Data
node1 = Data().store()
node2 = Int(3).store()
print(node1.pk)
print(node2.pk)
"""

        for flags, data_in_autogroup, int_in_autogroup in [
            [['--exclude', 'aiida.node:data'], False, True],
            [['--exclude', 'aiida.data:int'], True, False],
            [['--excludesubclasses', 'aiida.node:data'], False, False],
            [['--excludesubclasses', 'aiida.data:int'], True, False],
            [['--excludesubclasses', 'aiida.node:data', 'aiida.data:int'], False, False],
            [['--include', 'aiida.node:process'], False, False],
            [['--exclude', 'aiida.node:data', 'aiida.data:int'], False, False],
        ]:
            with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
                fhandle.write(script_content)
                fhandle.flush()

                options = [fhandle.name] + flags + ['--']
                result = self.cli_runner.invoke(cmd_run.run, options)
                self.assertClickResultNoException(result)

                pk1_str, pk2_str = result.output.split()
                pk1 = int(pk1_str)
                pk2 = int(pk2_str)
                _ = load_node(pk1)  # Check if the node can be loaded
                _ = load_node(pk2)  # Check if the node can be loaded

                queryb = QueryBuilder().append(Node, filters={'id': pk1}, tag='node')
                queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
                all_auto_groups_data = queryb.all()

                queryb = QueryBuilder().append(Node, filters={'id': pk2}, tag='node')
                queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
                all_auto_groups_int = queryb.all()
                self.assertEqual(
                    len(all_auto_groups_data), 1 if data_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the Data node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                self.assertEqual(
                    len(all_auto_groups_int), 1 if int_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the Int node '
                    "just created with flags '{}'".format(' '.join(flags))
                )

    def test_autogroup_clashing_label(self):
        """Check if the autogroup label is properly (re)generated when it clashes with an existing group name."""
        from aiida.orm import QueryBuilder, Node, Group, load_node

        script_content = """from aiida.orm import Data
node = Data().store()
print(node.pk)
"""
        autogroup_label = 'SOME_repeated_group_LABEL'
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            # First run
            options = [fhandle.name, '--group-label-prefix', autogroup_label]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded
            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )
            self.assertEqual(all_auto_groups[0][0].label, autogroup_label)

            # A few more runs with the same label - it should not crash but append something to the group name
            for _ in range(10):
                options = [fhandle.name, '--group-label-prefix', autogroup_label]
                result = self.cli_runner.invoke(cmd_run.run, options)
                self.assertClickResultNoException(result)

                pk = int(result.output)
                _ = load_node(pk)  # Check if the node can be loaded
                queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
                queryb.append(Group, with_node='node', filters={'type_string': 'auto.run'}, project='*')
                all_auto_groups = queryb.all()
                self.assertEqual(
                    len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
                )
                self.assertTrue(all_auto_groups[0][0].label.startswith(autogroup_label))
