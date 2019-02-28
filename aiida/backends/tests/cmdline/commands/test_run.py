# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi run`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands import cmd_run


class TestVerdiRun(AiidaTestCase):
    """Tests for `verdi run`."""

    def setUp(self):
        super(TestVerdiRun, self).setUp()
        self.cli_runner = CliRunner()

    def test_run_workfunction(self):
        """Regression test for #2165

        If the script that is passed to `verdi run` is not compiled correctly, running workfunctions from the script
        that are defined within the script will fail, as the inspect module will not correctly be able to determin
        the full path of the source file.
        """
        import tempfile
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
