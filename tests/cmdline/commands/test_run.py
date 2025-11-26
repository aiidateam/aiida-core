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

import pytest

from aiida.cmdline.commands import cmd_run
from aiida.common.log import override_log_level


class TestVerdiRun:
    """Tests for `verdi run`."""

    @pytest.mark.requires_rmq
    def test_run_workfunction(self, run_cli_command):
        """Regression test for #2165

        If the script that is passed to `verdi run` is not compiled correctly, running workfunctions from the script
        that are defined within the script will fail, as the inspect module will not correctly be able to determin
        the full path of the source file.
        """
        from aiida.orm import WorkFunctionNode, load_node

        source_file = textwrap.dedent(
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
        source_function = textwrap.dedent(
            """\
            @workfunction
            def wf():
                pass
            """
        )

        # If `verdi run` is not setup correctly, the script above when run with `verdi run` will fail, because when
        # the engine will try to create the node for the workfunction and create a copy of its sourcefile, namely the
        # script itself, it will use `inspect.getsourcefile` which will return None
        with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
            fhandle.write(source_file)
            fhandle.flush()

            options = [fhandle.name]
            result = run_cli_command(cmd_run.run, options, suppress_warnings=True, use_subprocess=True)

            # Try to load the function calculation node from the printed pk in the output
            pk = int(result.output.splitlines()[-1])
            node = load_node(pk)

            # Verify that the node has the correct function name and content
            assert isinstance(node, WorkFunctionNode)
            assert node.function_name == 'wf'
            assert node.get_source_code_file() == source_file
            assert node.get_source_code_function() == source_function


class TestAutoGroups:
    """Test the autogroup functionality."""

    def test_autogroup(self, run_cli_command):
        """Check if the autogroup is properly generated."""
        from aiida.orm import AutoGroup, Node, QueryBuilder, load_node

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
            result = run_cli_command(cmd_run.run, options, suppress_warnings=True, use_subprocess=True)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            assert len(all_auto_groups) == 1, 'There should be only one autogroup associated with the node just created'

    def test_autogroup_custom_label(self, run_cli_command):
        """Check if the autogroup is properly generated with the label specified."""
        from aiida.orm import AutoGroup, Node, QueryBuilder, load_node

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
            result = run_cli_command(cmd_run.run, options, suppress_warnings=True, use_subprocess=True)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            assert len(all_auto_groups) == 1, 'There should be only one autogroup associated with the node just created'
            assert all_auto_groups[0][0].label == autogroup_label

    def test_no_autogroup(self, run_cli_command):
        """Check if the autogroup is not generated if ``verdi run`` is asked not to."""
        from aiida.orm import AutoGroup, Node, QueryBuilder, load_node

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
            result = run_cli_command(cmd_run.run, options, suppress_warnings=True)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded

            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            assert len(all_auto_groups) == 0, 'There should be no autogroup generated'

    @pytest.mark.requires_rmq
    def test_autogroup_filter_class(self, run_cli_command):
        """Check if the autogroup is properly generated but filtered classes are skipped."""
        from aiida.orm import AutoGroup, Node, QueryBuilder, load_node

        script_content = textwrap.dedent(
            """\
            import sys
            from aiida.orm import Computer, Int, ArrayData, KpointsData, CalculationNode, WorkflowNode, InstalledCode
            from aiida.plugins import CalculationFactory
            from aiida.engine import run_get_node
            ArithmeticAdd = CalculationFactory('core.arithmetic.add')

            computer = Computer(
                label='localhost-example-{}'.format(sys.argv[1]),
                hostname='localhost',
                description='my computer',
                transport_type='core.local',
                scheduler_type='core.direct',
                workdir='/tmp'
            ).store()
            computer.configure()

            code = InstalledCode(
                default_calc_job_plugin='core.arithmetic.add',
                computer=computer,
                filepath_executable='/bin/true').store()
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
            print(node1.pk, node2.pk, node3.pk, node4.pk, node5.pk, node6.pk)
            """
        )

        for idx, (
            flags,
            kptdata_in_autogroup,
            arraydata_in_autogroup,
            int_in_autogroup,
            calc_in_autogroup,
            wf_in_autogroup,
            calcarithmetic_in_autogroup,
        ) in enumerate(
            [
                [['--exclude', 'aiida.data:core.array.kpoints'], False, True, True, True, True, True],
                # Check if % works anywhere - both 'int' and 'array.kpoints' contain an 'i'
                [['--exclude', 'aiida.data:core.%i%'], False, True, False, True, True, True],
                [['--exclude', 'aiida.data:core.int'], True, True, False, True, True, True],
                [['--exclude', 'aiida.data:%'], False, False, False, True, True, True],
                [
                    ['--exclude', 'aiida.data:core.array', 'aiida.data:core.array.%'],
                    False,
                    False,
                    True,
                    True,
                    True,
                    True,
                ],
                [
                    ['--exclude', 'aiida.data:core.array', 'aiida.data:core.array.%', 'aiida.data:core.int'],
                    False,
                    False,
                    False,
                    True,
                    True,
                    True,
                ],
                [['--exclude', 'aiida.calculations:core.arithmetic.add'], True, True, True, True, True, False],
                [
                    ['--include', 'aiida.node:process.calculation'],  # Base type, no specific plugin
                    False,
                    False,
                    False,
                    True,
                    False,
                    False,
                ],
                [
                    ['--include', 'aiida.node:process.workflow'],  # Base type, no specific plugin
                    False,
                    False,
                    False,
                    False,
                    True,
                    False,
                ],
                [[], True, True, True, True, True, True],
            ]
        ):
            with tempfile.NamedTemporaryFile(mode='w+') as fhandle:
                fhandle.write(script_content)
                fhandle.flush()

                options = ['--auto-group'] + flags + ['--', fhandle.name, str(idx)]
                with override_log_level():
                    result = run_cli_command(cmd_run.run, options)

                pk1_str, pk2_str, pk3_str, pk4_str, pk5_str, pk6_str = result.output_lines[-1].split()
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

                assert len(all_auto_groups_kptdata) == (1 if kptdata_in_autogroup else 0), (
                    'Wrong number of nodes in autogroup associated with the KpointsData node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                assert len(all_auto_groups_arraydata) == (1 if arraydata_in_autogroup else 0), (
                    'Wrong number of nodes in autogroup associated with the ArrayData node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                assert len(all_auto_groups_int) == (1 if int_in_autogroup else 0), (
                    'Wrong number of nodes in autogroup associated with the Int node '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                assert len(all_auto_groups_calc) == (1 if calc_in_autogroup else 0), (
                    'Wrong number of nodes in autogroup associated with the CalculationNode '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                assert len(all_auto_groups_wf) == (1 if wf_in_autogroup else 0), (
                    'Wrong number of nodes in autogroup associated with the WorkflowNode '
                    "just created with flags '{}'".format(' '.join(flags))
                )
                assert len(all_auto_groups_calcarithmetic) == (1 if calcarithmetic_in_autogroup else 0), (
                    'Wrong number of nodes in autogroup associated with the ArithmeticAdd CalcJobNode '
                    "just created with flags '{}'".format(' '.join(flags))
                )

    def test_autogroup_clashing_label(self, run_cli_command):
        """Check if the autogroup label is properly (re)generated when it clashes with an existing group name."""
        from aiida.orm import AutoGroup, Node, QueryBuilder, load_node

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
            result = run_cli_command(cmd_run.run, options, suppress_warnings=True, use_subprocess=True)

            pk = int(result.output)
            _ = load_node(pk)  # Check if the node can be loaded
            queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
            queryb.append(AutoGroup, with_node='node', project='*')
            all_auto_groups = queryb.all()
            assert len(all_auto_groups) == 1, 'There should be only one autogroup associated with the node just created'
            assert all_auto_groups[0][0].label == autogroup_label

            # A few more runs with the same label - it should not crash but append something to the group name
            for _ in range(10):
                options = [fhandle.name, '--auto-group', '--auto-group-label-prefix', autogroup_label]
                result = run_cli_command(cmd_run.run, options, suppress_warnings=True, use_subprocess=True)

                pk = int(result.output)
                _ = load_node(pk)  # Check if the node can be loaded
                queryb = QueryBuilder().append(Node, filters={'id': pk}, tag='node')
                queryb.append(AutoGroup, with_node='node', project='*')
                all_auto_groups = queryb.all()
                assert (
                    len(all_auto_groups) == 1
                ), 'There should be only one autogroup associated with the node just created'
                assert all_auto_groups[0][0].label.startswith(autogroup_label)
