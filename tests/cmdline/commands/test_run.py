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
import textwrap
import warnings

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
        from aiida.orm import load_node, WorkFunctionNode

        script_content = textwrap.dedent(
            """\
            #!/usr/bin/env python
            from aiida.engine import workfunction

            @workfunction
            def wf():
                pass

            if __name__ == '__main__':
                result, node = wf.run_get_node()
                print(node.pk)
            """
        )

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
        # I need to disable the global variable of this test environment, because invoke is just calling the function
        # and therefore inheriting the global variable
        self._old_autogroup = autogroup.CURRENT_AUTOGROUP
        autogroup.CURRENT_AUTOGROUP = None

    def tearDown(self):
        """Setup the CLI runner to run command line commands."""
        from aiida.orm import autogroup

        super().tearDown()
        autogroup.CURRENT_AUTOGROUP = self._old_autogroup

    def test_autogroup(self):
        """Check if the autogroup is properly generated."""
        from aiida.orm import QueryBuilder, Node, AutoGroup, load_node

        script_content = textwrap.dedent(
            """\
            from aiida.orm import Data
            node = Data().store()
            print(node.pk)
            """
        )

        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = ['--auto-group', fhandle.name]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )

    def test_autogroup_custom_label(self):
        """Check if the autogroup is properly generated with the label specified."""
        from aiida.orm import QueryBuilder, Node, AutoGroup, load_node

        script_content = textwrap.dedent(
            """\
            from aiida.orm import Data
            node = Data().store()
            print(node.pk)
            """
        )

        autogroup_label = 'SOME_group_LABEL'
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = [fhandle.name, '--auto-group', '--auto-group-label-prefix', autogroup_label]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )
            self.assertEqual(all_auto_groups[0][0].label, autogroup_label)

    def test_no_autogroup(self):
        """Check if the autogroup is not generated if ``verdi run`` is asked not to."""
        from aiida.orm import QueryBuilder, Node, AutoGroup, load_node

        script_content = textwrap.dedent(
            """\
            from aiida.orm import Data
            node = Data().store()
            print(node.pk)
            """
        )

        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = [fhandle.name]  # Not storing an autogroup by default
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(len(all_auto_groups), 0, 'There should be no autogroup generated')

    def test_autogroup_filter_class(self):  # pylint: disable=too-many-locals
        """Check if the autogroup is properly generated but filtered classes are skipped."""
        from aiida.orm import Code, QueryBuilder, Node, AutoGroup, load_node

        script_content = textwrap.dedent(
            """\
            import sys
            from aiida.orm import Computer, Int, ArrayData, KpointsData, CalculationNode, WorkflowNode
            from aiida.plugins import CalculationFactory
            from aiida.engine import run_get_node
            ArithmeticAdd = CalculationFactory('arithmetic.add')

            computer = Computer(
                name='localhost-example-{}'.format(sys.argv[1]),
                hostname='localhost',
                description='my computer',
                transport_type='local',
                scheduler_type='direct',
                workdir='/tmp'
            ).store()
            computer.configure()

            code = Code(
                input_plugin_name='arithmetic.add',
                remote_computer_exec=[computer, '/bin/true']).store()
            inputs = {
                'x': Int(1),
                'y': Int(2),
                'code': code,
                'metadata': {
                    'options': {
                        'resources': {
                            'num_machines': 1,
                            'num_mpiprocs_per_machine': 1
                        }
                    }
                }
            }

            node1 = KpointsData().store()
            node2 = ArrayData().store()
            node3 = Int(3).store()
            node4 = CalculationNode().store()
            node5 = WorkflowNode().store()
            _, node6 = run_get_node(ArithmeticAdd, **inputs)
            print(node1.pk)
            print(node2.pk)
            print(node3.pk)
            print(node4.pk)
            print(node5.pk)
            print(node6.pk)
            """
        )

        Code()
        for idx, (
            flags,
            kptdata_in_autogroup,
            arraydata_in_autogroup,
            int_in_autogroup,
            calc_in_autogroup,
            wf_in_autogroup,
            calcarithmetic_in_autogroup,
        ) in enumerate([
            [['--exclude', 'aiida.data:array.kpoints'], False, True, True, True, True, True],
            # Check if % works anywhere - both 'int' and 'array.kpoints' contain an 'i'
            [['--exclude', 'aiida.data:%i%'], False, True, False, True, True, True],
            [['--exclude', 'aiida.data:int'], True, True, False, True, True, True],
            [['--exclude', 'aiida.data:%'], False, False, False, True, True, True],
            [['--exclude', 'aiida.data:array', 'aiida.data:array.%'], False, False, True, True, True, True],
            [['--exclude', 'aiida.data:array', 'aiida.data:array.%', 'aiida.data:int'], False, False, False, True, True,
             True],
            [['--exclude', 'aiida.calculations:arithmetic.add'], True, True, True, True, True, False],
            [
                ['--include', 'aiida.node:process.calculation'],  # Base type, no specific plugin
                False,
                False,
                False,
                True,
                False,
                False
            ],
            [
                ['--include', 'aiida.node:process.workflow'],  # Base type, no specific plugin
                False,
                False,
                False,
                False,
                True,
                False
            ],
            [[], True, True, True, True, True, True],
        ]):
            with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
                fhandle.write(script_content)
                fhandle.flush()

                options = ['--auto-group'] + flags + ['--', fhandle.name, str(idx)]
                result = self.cli_runner.invoke(cmd_run.run, options)
                self.assertClickResultNoException(result)

                pk1_str, pk2_str, pk3_str, pk4_str, pk5_str, pk6_str = result.output.split()
                pk1 = int(pk1_str)
                pk2 = int(pk2_str)
                pk3 = int(pk3_str)
                pk4 = int(pk4_str)
                pk5 = int(pk5_str)
                pk6 = int(pk6_str)
                _ = load_node(pk1)  # Check if the node can be loaded
                _ = load_node(pk2)  # Check if the node can be loaded
                _ = load_node(pk3)  # Check if the node can be loaded
                _ = load_node(pk4)  # Check if the node can be loaded
                _ = load_node(pk5)  # Check if the node can be loaded
                _ = load_node(pk6)  # Check if the node can be loaded

                queryb = QueryBuilder().append(Node, filters={'id': pk1}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups_kptdata = queryb.all()

                queryb = QueryBuilder().append(Node, filters={'id': pk2}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups_arraydata = queryb.all()

                queryb = QueryBuilder().append(Node, filters={'id': pk3}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups_int = queryb.all()

                queryb = QueryBuilder().append(Node, filters={'id': pk4}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups_calc = queryb.all()

                queryb = QueryBuilder().append(Node, filters={'id': pk5}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups_wf = queryb.all()

                queryb = QueryBuilder().append(Node, filters={'id': pk6}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups_calcarithmetic = queryb.all()

                self.assertEqual(
                    len(all_auto_groups_kptdata), 1 if kptdata_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the KpointsData node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                self.assertEqual(
                    len(all_auto_groups_arraydata), 1 if arraydata_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the ArrayData node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                self.assertEqual(
                    len(all_auto_groups_int), 1 if int_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the Int node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                self.assertEqual(
                    len(all_auto_groups_calc), 1 if calc_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the CalculationNode '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                self.assertEqual(
                    len(all_auto_groups_wf), 1 if wf_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the WorkflowNode '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                self.assertEqual(
                    len(all_auto_groups_calcarithmetic), 1 if calcarithmetic_in_autogroup else 0,
                    'Wrong number of nodes in autogroup associated with the ArithmeticAdd CalcJobNode '
                    "just created with flags '{}'".format(' '.join(flags))
                )

    def test_autogroup_clashing_label(self):
        """Check if the autogroup label is properly (re)generated when it clashes with an existing group name."""
        from aiida.orm import QueryBuilder, Node, AutoGroup, load_node

        script_content = textwrap.dedent(
            """\
            from aiida.orm import Data
            node = Data().store()
            print(node.pk)
            """
        )

        autogroup_label = 'SOME_repeated_group_LABEL'
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            # First run
            options = [fhandle.name, '--auto-group', '--auto-group-label-prefix', autogroup_label]
            result = self.cli_runner.invoke(cmd_run.run, options)
            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded
            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )
            self.assertEqual(all_auto_groups[0][0].label, autogroup_label)

            # A few more runs with the same label - it should not crash but append something to the group name
            for _ in range(10):
                options = [fhandle.name, '--auto-group', '--auto-group-label-prefix', autogroup_label]
                result = self.cli_runner.invoke(cmd_run.run, options)
                self.assertClickResultNoException(result)

                pk = int(result.output)
                _ = load_node(pk)  # Check if the node can be loaded
                queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups = queryb.all()
                self.assertEqual(
                    len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
                )
                self.assertTrue(all_auto_groups[0][0].label.startswith(autogroup_label))

    def test_legacy_autogroup_name(self):
        """Check if the autogroup is properly generated when using the legacy --group-name flag."""
        from aiida.orm import QueryBuilder, Node, AutoGroup, load_node

        script_content = textwrap.dedent(
            """\
            from aiida.orm import Data
            node = Data().store()
            print(node.pk)
            """
        )
        group_label = 'legacy-group-name'

        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(script_content)
            fhandle.flush()

            options = ['--group-name', group_label, fhandle.name]
            with warnings.catch_warnings(record=True) as warns:  # pylint: disable=no-member
                result = self.cli_runner.invoke(cmd_run.run, options)
                self.assertTrue(
                    any(['use `--auto-group-label-prefix` instead' in str(warn.message) for warn in warns]),
                    "No warning for '--group-name' was raised"
                )

            self.assertClickResultNoException(result)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            self.assertEqual(
                len(all_auto_groups), 1, 'There should be only one autogroup associated with the node just created'
            )
            self.assertEqual(
                all_auto_groups[0][0].label, group_label,
                'The auto group label is "{}" instead of "{}"'.format(all_auto_groups[0][0].label, group_label)
            )
